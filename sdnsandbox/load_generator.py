import logging
from abc import ABC, abstractmethod
from collections import namedtuple
from math import pi, sin
from os import makedirs
from os.path import join as pj
from subprocess import STDOUT, TimeoutExpired
from time import monotonic
from enum import Enum


class Protocol(Enum):
    UDP = 0
    TCP = 1


logger = logging.getLogger(__name__)


class LoadGeneratorFactory(object):
    @staticmethod
    def create(load_generator_conf):
        if load_generator_conf["type"] == "DITG":
            if load_generator_conf["protocol"] == "UDP":
                protocol = Protocol.UDP
            elif load_generator_conf["protocol"] == "TCP":
                protocol = Protocol.TCP
            else:
                raise ValueError("Unknown protocol=%s" % load_generator_conf["protocol"])
            return DITGLoadGenerator(protocol,
                                     load_generator_conf["periods"],
                                     load_generator_conf["period_seconds"],
                                     load_generator_conf["pps_baseline"],
                                     load_generator_conf["pps_amplitude"],
                                     load_generator_conf["pps_wavelength"])
        else:
            raise ValueError("Unknown topology type=%s" % load_generator_conf["type"])


class LoadGenerator(ABC):
    def __init__(self):
        self.receivers = []
        self.senders = []

    @abstractmethod
    def start_receivers(self, network, output_path):
        return self.receivers

    @abstractmethod
    def run_senders(self, network, output_path):
        return self.senders

    @abstractmethod
    def stop_receivers(self):
        pass


class DITGLoadGenerator(LoadGenerator):
    Receiver = namedtuple("Receiver", "process, logfile")
    Sender = namedtuple("Sender", "process, start_time, logfile")

    def __init__(self, protocol, periods, period_duration_seconds, pps_base_level, pps_amplitude, pps_wavelength):
        super().__init__()
        self.protocol = protocol
        self.periods = periods
        self.period_duration_seconds = period_duration_seconds
        self.pps_base_level = pps_base_level
        self.pps_amplitude = pps_amplitude
        self.pps_wavelength = pps_wavelength

    def start_receivers(self, network, output_path):
        logger.info("Adding ITGRecv to all network hosts")
        logs_path = pj(output_path, "logs", "receivers")
        makedirs(logs_path)
        itg_recv_cmd = 'while [ 1 ]; do ' \
                       'echo [$(date)] Starting ITGRecv;' \
                       'ITGRecv;' \
                       'echo [$(date)] ITGRecv Stopped;' \
                       'done'
        self.receivers = []
        for host in network.hosts:
            log_path = pj(logs_path, "receiver-" + host.IP() + ".log")
            logfile = open(log_path, 'w')
            itg_recv = host.popen(itg_recv_cmd, shell=True, stderr=STDOUT, stdout=logfile)
            self.receivers.append(self.Receiver(itg_recv, logfile))

    def run_senders(self, network, output_path):
        logger.info("Running ITGSenders")
        logs_path = pj(output_path, "logs", "senders")
        makedirs(logs_path)
        host_addresses = [host.IP() for host in network.hosts]
        for period in range(self.periods):
            for host_index, host in enumerate(network.hosts):
                dest = self.calculate_destination(period, host_index, host_addresses)
                host_senders = self.run_host_senders(host, dest, logs_path, period)
                self.senders.extend(host_senders)
            # TODO: make sure the sender filled the whole duration with packets (rerun after crash)?
            for sender in self.senders:
                time_passed = monotonic() - sender.start_time
                timeout = self.period_duration_seconds - time_passed
                try:
                    sender.process.wait(timeout=timeout)
                except TimeoutExpired as e:
                    logger.error("Sender timed out: %s", str(e))
                sender.logfile.close()
            self.senders = []

    def run_host_senders(self, host, dest, logs_path, period):
        host_senders = []
        itg_send_opts = self.calculate_send_opts(period, dest)
        for opts in itg_send_opts.items():
            itg_send_cmd = 'ITGSend ' + opts[1]
            log_path = pj(logs_path, "sender-" + host.IP() + "-" + opts[0] + ".log")
            logfile = open(log_path, 'a')
            start_time = monotonic()
            itg_send = host.popen(itg_send_cmd, stderr=STDOUT, stdout=logfile)
            host_senders.append(self.Sender(itg_send, start_time, logfile))
        return host_senders

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
        # 2pi is the regular wavelength of sine, so we divide it by the required wavelength to get the amplitude change
        period_pps = self.pps_base_level + int(self.pps_amplitude*sin(2*pi*period/self.pps_wavelength))
        # All values based roughly on http://www.caida.org/research/traffic-analysis/AIX/plen_hist/
        # The IMIX split shown was ~30% 40B, ~55% normal around 576B, ~15% 1500B
        # The 190 standard deviation makes 3-sigma between 50-1400 packet sizes be 99,7%
        if self.protocol == Protocol.UDP:
            # To get a similar distribution with UDP:
            # Constant packet size - 40B 30%
            send_opts['send_40bytes'] = '-a %s -T UDP -t %d -c 40 -C %d' % (dest,
                                                                            self.period_duration_seconds*1000,
                                                                            int(0.3 * period_pps))
            # Normal Distribution for packet sizes - 55%
            send_opts['send_normal'] = '-a %s -T UDP -t %d -n 576, 190 -C %d' % (dest,
                                                                                 self.period_duration_seconds*1000,
                                                                                 int(0.55 * period_pps))
            # Constant packet size - 1500B - 15%
            send_opts['send_1500B'] = '-a %s -T UDP -t %d -c 1500 -C %d' % (dest,
                                                                            self.period_duration_seconds*1000,
                                                                            int(0.15 * period_pps))
        elif self.protocol == Protocol.TCP:
            # To get a similar distribution with TCP (which has builtin 40B ACKs):
            # Normal distribution with [100 - (100 * 15 / (15 + 55))] = 78%
            send_opts['send_normal'] = '-a %s -T UDP -t %d -n 576, 190 -C %d' % (dest,
                                                                                 self.period_duration_seconds*1000,
                                                                                 int(0.78 * period_pps))
            # Constant packet size - 1500B - 22%
            pps_high = int(0.15 * period_pps)
            send_opts['send_1500B'] = '-a %s -T UDP -t %d -c 1500 -C %d' % (dest,
                                                                            self.period_duration_seconds*1000,
                                                                            int(0.22 * period_pps))
        else:
            raise RuntimeError("Unknown protocol defined for senders!")
        return send_opts
