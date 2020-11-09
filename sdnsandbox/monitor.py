from abc import ABC, abstractmethod
import logging
from sdnsandbox.util import run_script
from subprocess import Popen
from shutil import which


class MonitorFactory(object):
    @staticmethod
    def create(monitor_conf):
        if monitor_conf["type"] == "sflow":
            return SFlowMonitor()
        else:
            raise ValueError("Unknown monitor type=%s" % monitor_conf["type"])


class Monitor(ABC):
    @abstractmethod
    def start_monitoring(self):
        pass

    @abstractmethod
    def save_monitoring_data_and_stop(self, output_path):
        pass


class SFlowMonitor(Monitor):
    """A Monitor using an sFlow collector process and OvS-embedded sFlow monitoring"""
    sflow_keys_to_monitor =\
        "unixSecondsUTC,ifIndex,ifInOctets,ifInDiscards,ifInErrors,ifOutOctets,ifOutDiscards,ifOutErrors"
    sflowtool_cmd = "sflowtool"

    def __init__(self):
        if which(self.sflowtool_cmd) is None:
            raise RuntimeError("command %s is not available, can't setup sFlow monitoring" % self.sflowtool_cmd)
        self.sflowtool_proc = None

    def start_monitoring(self):
        if self.sflowtool_proc is None:
            logging.info("Starting sFlow monitoring")
            logging.info("Creating sFlow monitoring instances in the ovs switches")
            run_script("set_ovs_sflow.sh")
            logging.info("Starting sflowtool to record monitoring data")
            self.sflowtool_proc = Popen([self.sflowtool_cmd, "-k", "-L", self.sflow_keys_to_monitor])
        else:
            logging.error("Monitoring is already running")

    def save_monitoring_data_and_stop(self, output_path):
        if self.sflowtool_proc is not None:
            logging.info("Stopping sflowtool")
            self.sflowtool_proc.terminate()
            with open(output_path, 'w') as md:
                md.write(self.sflowtool_proc.stdout)
        else:
            logging.error("No monitoring running to stop")
