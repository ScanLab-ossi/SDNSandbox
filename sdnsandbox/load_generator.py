import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import pi, sin
from os import makedirs
from os.path import join as pj
from subprocess import STDOUT
from time import monotonic, sleep
from typing import IO, List
import dacite

from sdnsandbox.util import ensure_cmd_exists

from mininet.node import Host


class Protocol(Enum):
    UDP = 0
    TCP = 1

    @staticmethod
    def from_str(protocol: str):
        if protocol == "UDP":
            return Protocol.UDP
        elif protocol == "TCP":
            return Protocol.TCP
        else:
            raise ValueError("Unknown protocol=%s" % protocol)


logger = logging.getLogger(__name__)


class LoadGeneratorFactory:
    @staticmethod
    def create(load_generator_conf):
        if load_generator_conf["type"] == "DITG-IMIX":
            config = dacite.from_dict(data_class=DITGConfig, data=load_generator_conf,
                                      config=dacite.Config(type_hooks={Protocol: lambda p: Protocol.from_str(p)}))
            return DitgImixLoadGenerator(config)
        elif load_generator_conf["type"] == "NPING-UDP-IMIX":
            config = dacite.from_dict(data_class=NpingConfig, data=load_generator_conf)
            return NpingUDPImixLoadGenerator(config)
        else:
            raise ValueError("Unknown topology type=%s" % load_generator_conf["type"])


@dataclass
class Receiver:
    process: subprocess.Popen
    logfile: IO


@dataclass
class Sender:
    host: Host
    process: subprocess.Popen
    start_time: float
    logfile: IO


@dataclass
class LoadGenerator(ABC):
    receivers: List[Receiver]
    senders: List[Sender]

    @abstractmethod
    def start_receivers(self, hosts: List[Host], output_path: str, logs_path=''):
        pass

    @abstractmethod
    def run_senders(self, hosts: List[Host], output_path: str, logs_path=''):
        pass

    @abstractmethod
    def stop_receivers(self):
        pass


@dataclass
class DITGConfig:
    protocol: Protocol
    periods: int
    period_duration_seconds: int
    pps_base_level: int
    pps_amplitude: int
    pps_wavelength: int
    disable_cmd_ensure: bool = False
    warmup_seconds: int = 0


class DitgImixLoadGenerator(LoadGenerator):
    def __init__(self, config: DITGConfig):
        super().__init__([], [])
        failure_msg = "Can't setup D-ITG load generation!"
        if not config.disable_cmd_ensure:
            ensure_cmd_exists("ITGRecv", failure_msg)
            ensure_cmd_exists("ITGSend", failure_msg)
        self.config = config

    def start_receivers(self, hosts, output_path, logs_path=''):
        logger.info("Adding ITGRecv to all network hosts")
        if logs_path == '':
            logs_path = pj(output_path, "logs", "receivers")
            makedirs(logs_path)
        itg_recv_cmd = 'while [ 1 ]; do ' \
                       'echo [$(date)] Starting ITGRecv;' \
                       'ITGRecv;' \
                       'echo [$(date)] ITGRecv Stopped;' \
                       'done'
        self.receivers = []
        for host in hosts:
            log_path = pj(logs_path, "receiver-" + host.IP() + ".log")
            logfile = open(log_path, 'w')
            itg_recv = host.popen(itg_recv_cmd, shell=True, stderr=STDOUT, stdout=logfile)
            self.receivers.append(Receiver(itg_recv, logfile))

    def run_senders(self, hosts, output_path, logs_path=''):
        logger.info("Running ITGSenders")
        if logs_path == '':
            logs_path = pj(output_path, "logs", "senders")
            makedirs(logs_path)
        host_addresses = [host.IP() for host in hosts]
        for period in range(self.config.periods):
            for host_index, host in enumerate(hosts):
                dest = self.calculate_destination(period, host_index, host_addresses)
                host_senders = self.run_host_senders(host, dest, logs_path, period)
                self.senders.extend(host_senders)
            success, timeout_terminated, failure, reruns = 0, 0, 0, 0
            period_start = monotonic()
            while monotonic() - period_start < self.config.period_duration_seconds:
                for sender in self.senders:
                    return_code = sender.process.poll()
                    if return_code not in [0, None]:
                        logger.debug("Found crashed sender at %s, after %d seconds with cmd %s",
                                     sender.host.IP(),
                                     int(monotonic() - sender.start_time),
                                     str(sender.process.args))
                        # make sure the log was already flushed before rerun
                        sender.logfile.flush()
                        # rerun sender
                        self.run_sender(sender.host, sender.process.args, sender.logfile)
                        reruns += 1
                # avoid busy waiting
                sleep(0.1)
            for sender in self.senders:
                return_code = sender.process.poll()
                if return_code is None:
                    logger.debug("Sender timed out and will be killed: %s", sender.process.args)
                    # forcibly stop senders that took too long
                    sender.process.kill()
                    timeout_terminated += 1
                elif return_code != 0:
                    failure += 1
                else:
                    success += 1
                sender.logfile.close()
            self.senders = []
            logger.info(
                "For period=%d we had "
                "%d successfully completed senders, "
                "%d sender reruns due to failure (probably a D-ITG issue), "
                "%d senders we terminated due to timeout "
                "and %d senders who finished the period in a failed state",
                period, success, reruns, timeout_terminated, failure)

    def run_host_senders(self, host, dest, logs_path, period):
        host_senders = []
        itg_send_opts = self.calculate_send_opts(period, dest)
        for opts in itg_send_opts.items():
            itg_send_cmd = 'ITGSend ' + opts[1]
            log_path = pj(logs_path, "sender-" + host.IP() + "-" + opts[0] + ".log")
            logfile = open(log_path, 'a')
            itg_send = self.run_sender(host, itg_send_cmd, logfile)
            host_senders.append(Sender(host, itg_send, monotonic(), logfile))
        return host_senders

    @staticmethod
    def run_sender(host, itg_send_cmd, logfile):
        logfile.write(str(datetime.now()) + ": Starting ITGSend with cmd='" + str(itg_send_cmd) + "'\n")
        logfile.flush()
        itg_send = host.popen(itg_send_cmd, stderr=STDOUT, stdout=logfile)
        return itg_send

    def stop_receivers(self):
        logger.info("Killing ITGRecv(s)...")
        for receiver in self.receivers:
            receiver.process.terminate()
            receiver.logfile.close()

    @staticmethod
    def calculate_destination(period, host_id, other_addresses):
        period_dest_index = (period - 1) + (host_id - 1)
        return other_addresses[period_dest_index % len(other_addresses)]

    def calculate_send_opts(self, period, dest):
        send_opts = {}
        # allow sender warmup period
        duration_ms = (self.config.period_duration_seconds - self.config.warmup_seconds) * 1000
        # 2pi is the regular wavelength of sine, so we divide it by the required wavelength to get the amplitude change
        period_pps = self.config.pps_base_level + int(
            self.config.pps_amplitude * sin(2 * pi * period / self.config.pps_wavelength))
        # All values based roughly on http://www.caida.org/research/traffic-analysis/AIX/plen_hist/
        # The IMIX split shown was ~30% 40B, ~55% normal around 576B, ~15% 1500B
        # The 190 standard deviation makes 3-sigma between 50-1400 packet sizes be 99,7%
        if self.config.protocol == Protocol.UDP:
            # To get a similar distribution with UDP:
            # Constant packet size - 40B 30%
            send_opts['send_40bytes'] = '-a %s -T UDP -t %d -c 40 -C %d' % (dest,
                                                                            duration_ms,
                                                                            int(0.3 * period_pps))
            # Normal Distribution for packet sizes - 55%
            send_opts['send_normal'] = '-a %s -T UDP -t %d -n 576, 190 -C %d' % (dest,
                                                                                 duration_ms,
                                                                                 int(0.55 * period_pps))
            # Constant packet size - 1500B - 15%
            # Actual UDP packet payload is 1472 after removing layer2-4 headers
            send_opts['send_1500B'] = '-a %s -T UDP -t %d -c 1472 -C %d' % (dest,
                                                                            duration_ms,
                                                                            int(0.15 * period_pps))
        elif self.config.protocol == Protocol.TCP:
            # To get a similar distribution with TCP (which has builtin 40B ACKs):
            # Normal distribution with [100 - (100 * 15 / (15 + 55))] = 78%
            send_opts['send_normal'] = '-a %s -T UDP -t %d -n 576, 190 -C %d' % (dest,
                                                                                 duration_ms,
                                                                                 int(0.78 * period_pps))
            # Constant packet size - 1500B - 22%
            send_opts['send_1500B'] = '-a %s -T UDP -t %d -c 1500 -C %d' % (dest,
                                                                            duration_ms,
                                                                            int(0.22 * period_pps))
        else:
            raise RuntimeError("Unknown protocol defined for senders!")
        return send_opts


@dataclass
class NpingConfig:
    periods: int
    period_duration_seconds: int
    pps_base_level: int
    pps_amplitude: int
    pps_wavelength: int
    disable_cmd_ensure: bool = False
    listen_port: int = 10000
    verbosity_level: int = -1


class NpingUDPImixLoadGenerator(LoadGenerator):
    def __init__(self, config: NpingConfig):
        super().__init__([], [])
        failure_msg = "Can't setup Nping load generation!"
        if not config.disable_cmd_ensure:
            ensure_cmd_exists("ncat", failure_msg)
            ensure_cmd_exists("nping", failure_msg)
        self.config = config

    def start_receivers(self, hosts, output_path, logs_path=''):
        logger.info("Adding ncat listener to all network hosts")
        if logs_path == '':
            logs_path = pj(output_path, "logs", "receivers")
            makedirs(logs_path)
        itg_recv_cmd = 'while [ 1 ]; do ' \
                       'echo [$(date)] Starting ncat;' \
                       'ncat -4 -l %d --keep-open --udp --sh-exec "cat > /dev/null";' \
                       'echo [$(date)] ncat Stopped;' \
                       'done' % self.config.listen_port
        self.receivers = []
        for host in hosts:
            log_path = pj(logs_path, "receiver-" + host.IP() + ".log")
            logfile = open(log_path, 'w')
            itg_recv = host.popen(itg_recv_cmd, shell=True, stderr=STDOUT, stdout=logfile)
            self.receivers.append(Receiver(itg_recv, logfile))

    def run_senders(self, hosts, output_path, logs_path=''):
        logger.info("Running Npings")
        if logs_path == '':
            logs_path = pj(output_path, "logs", "senders")
            makedirs(logs_path)
        host_addresses = [host.IP() for host in hosts]
        for period in range(self.config.periods):
            for host_index, host in enumerate(hosts):
                dest = self.calculate_destination(period, host_index, host_addresses)
                host_senders = self.run_host_senders(host, dest, logs_path, period)
                self.senders.extend(host_senders)
            success, timeout_terminated, failure = 0, 0, 0
            for sender in self.senders:
                time_spent = monotonic() - sender.start_time
                time_left = self.config.period_duration_seconds - time_spent
                if time_left > 0:
                    sleep(time_left)
                return_code = sender.process.poll()
                if return_code is None:
                    logger.debug("Sender timed out and will be killed: %s", sender.process.args)
                    # forcibly stop senders that took too long
                    sender.process.kill()
                    timeout_terminated += 1
                elif return_code != 0:
                    failure += 1
                else:
                    success += 1
                sender.logfile.close()
            self.senders = []
            logger.info(
                "For period=%d we had "
                "%d successfully completed senders, "
                "%d senders we terminated due to timeout "
                "and %d senders who finished the period in a failed state",
                period, success, timeout_terminated, failure)

    @staticmethod
    def calculate_destination(period, host_id, other_addresses):
        period_dest_index = (period - 1) + (host_id - 1)
        return other_addresses[period_dest_index % len(other_addresses)]

    def run_host_senders(self, host, dest, logs_path, period):
        host_senders = []
        itg_send_opts = self.calculate_send_opts(period, dest)
        for opts in itg_send_opts.items():
            nping_send_cmd = 'nping --udp -p %d -v%d ' % (self.config.listen_port, self.config.verbosity_level)
            nping_send_cmd += opts[1]
            log_path = pj(logs_path, "sender-" + host.IP() + "-" + opts[0] + ".log")
            logfile = open(log_path, 'a')
            nping_send = self.run_sender(host, nping_send_cmd, logfile)
            host_senders.append(Sender(host, nping_send, monotonic(), logfile))
        return host_senders

    @staticmethod
    def run_sender(host, nping_send_cmd, logfile):
        logfile.write(str(datetime.now()) + ": Starting Nping with cmd='" + str(nping_send_cmd) + "'\n")
        logfile.flush()
        nping_send = host.popen(nping_send_cmd, stderr=STDOUT, stdout=logfile)
        return nping_send

    def calculate_send_opts(self, period, dest):
        send_opts = {}
        # 2pi is the regular wavelength of sine, so we divide it by the required wavelength to get the amplitude change
        period_pps = self.config.pps_base_level + int(
            self.config.pps_amplitude * sin(2 * pi * period / self.config.pps_wavelength))
        # All values based roughly on http://www.caida.org/research/traffic-analysis/AIX/plen_hist/
        # The IMIX split shown was ~30% 40B, ~55% normal around 576B, ~15% 1500B
        # The 190 standard deviation makes 3-sigma between 50-1400 packet sizes be 99,7%
        # To get a similar distribution with UDP:
        # Constant packet size - 40B 30%
        rate = int(0.3 * period_pps)
        send_opts['send_40bytes'] = '--dest-ip %s --data-length 40 --rate %d --count %d' % \
                                    (dest,
                                     rate,
                                     rate * self.config.period_duration_seconds)
        # Approx. of the Normal Distribution for packet sizes - 55%
        half_normal_pps = int(0.55 * 0.5 * period_pps)
        quarter_normal_pps = half_normal_pps / 2
        send_opts['send_normal_low'] = '--dest-ip %s --data-length 448 --rate %d --count %d' % \
                                       (dest,
                                        quarter_normal_pps,
                                        quarter_normal_pps * self.config.period_duration_seconds)
        send_opts['send_normal_mid'] = '--dest-ip %s --data-length 576 --rate %d --count %d' % \
                                       (dest,
                                        half_normal_pps,
                                        half_normal_pps * self.config.period_duration_seconds)
        send_opts['send_normal_high'] = '--dest-ip %s --data-length 704 --rate %d --count %d' % \
                                        (dest,
                                         quarter_normal_pps,
                                         quarter_normal_pps * self.config.period_duration_seconds)
        # Constant packet size - 1500B - 15%
        rate /= 2
        # Actual UDP packet payload is 1472 after removing layer2-4 headers/footers
        send_opts['send_1500B'] = '--dest-ip %s --data-length 1472 --rate %d --count %d' % \
                                  (dest,
                                   rate,
                                   rate * self.config.period_duration_seconds)
        return send_opts

    def stop_receivers(self):
        logger.info("Killing ncat(s)...")
        for receiver in self.receivers:
            receiver.process.terminate()
            receiver.logfile.close()
