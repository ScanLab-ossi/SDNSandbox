from abc import ABC, abstractmethod
import logging
from sdnsandbox.util import run_script
from subprocess import Popen, STDOUT
from shutil import which
from os.path import join as pj


class MonitorFactory(object):
    @staticmethod
    def create(monitor_conf):
        if monitor_conf["type"] == "sflow":
            return SFlowMonitor(monitor_conf["csv_filename"])
        else:
            raise ValueError("Unknown monitor type=%s" % monitor_conf["type"])


class Monitor(ABC):
    @abstractmethod
    def start_monitoring(self, output_path):
        pass

    @abstractmethod
    def stop_monitoring(self):
        pass


class SFlowMonitor(Monitor):
    """A Monitor using an sFlow collector process and OvS-embedded sFlow monitoring"""
    sflow_keys_to_monitor =\
        "unixSecondsUTC,ifIndex,ifInOctets,ifInDiscards,ifInErrors,ifOutOctets,ifOutDiscards,ifOutErrors"
    sflowtool_cmd = "sflowtool"

    def __init__(self, csv_filename):
        if which(self.sflowtool_cmd) is None:
            raise RuntimeError("command %s is not available, can't setup sFlow monitoring" % self.sflowtool_cmd)
        self.sflowtool_proc = None
        self.csv_filename = csv_filename
        self.output_file = None

    def start_monitoring(self, output_path):
        if self.sflowtool_proc is None:
            logging.info("Starting sFlow monitoring")
            logging.info("Creating sFlow monitoring instances in the ovs switches")
            run_script("set_ovs_sflow.sh")
            logging.info("Starting sflowtool to record monitoring data to: %s" % output_path)
            self.output_file = open(pj(output_path, self.csv_filename), 'w')
            self.sflowtool_proc = Popen([self.sflowtool_cmd, "-k", "-L", self.sflow_keys_to_monitor],
                                        stderr=STDOUT, stdout=self.output_file)
        else:
            logging.error("Monitoring is already running")

    def stop_monitoring(self):
        if self.sflowtool_proc is not None:
            logging.info("Stopping sflowtool")
            self.sflowtool_proc.terminate()
            self.output_file.close()
        else:
            logging.error("No monitoring running to stop")
