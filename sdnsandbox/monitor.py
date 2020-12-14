from abc import ABC, abstractmethod
import logging
from json import dump
import pandas as pd

from sdnsandbox.util import run_script, get_inter_switch_port_interfaces
from subprocess import Popen, STDOUT
from shutil import which
from os.path import join as pj
from os import remove


logger = logging.getLogger(__name__)


class MonitorFactory(object):
    @staticmethod
    def create(monitor_conf):
        if monitor_conf["type"] == "sflow":
            return SFlowMonitor(monitor_conf["data_key"],
                                monitor_conf["normalize_by"],
                                monitor_conf["csv_filename"],
                                monitor_conf.get("interfaces_filename"),
                                monitor_conf.get("hd5_filename", monitor_conf["csv_filename"]+".hd5"))
        else:
            raise ValueError("Unknown monitor type=%s" % monitor_conf["type"])


class Monitor(ABC):
    @abstractmethod
    def start_monitoring(self, output_path):
        pass

    @abstractmethod
    def stop_monitoring_and_save(self, output_path):
        pass


class SFlowMonitor(Monitor):
    """A Monitor using an sFlow collector process and OvS-embedded sFlow monitoring"""
    sflow_time_key = "unixSecondsUTC"
    sflow_intf_index_key = "ifIndex"
    sflowtool_cmd = "sflowtool"

    def __init__(self, data_key, normalize_by, csv_filename, interfaces_filename, hd5_filename, pandas_processing=True):
        if which(self.sflowtool_cmd) is None:
            raise RuntimeError("command %s is not available, can't setup sFlow monitoring" % self.sflowtool_cmd)
        self.sflow_keys_to_monitor = [self.sflow_time_key, self.sflow_intf_index_key, data_key]
        self.normalize_by = normalize_by
        self.csv_filename = csv_filename
        self.interfaces_filename = interfaces_filename
        self.sflowtool_proc = None
        self.output_file = None
        self.hd5_filename = hd5_filename
        self.interfaces = None
        self.samples_processor = self.get_samples_pandas if pandas_processing else self.get_samples

    def start_monitoring(self, output_path):
        if self.sflowtool_proc is None:
            logger.info("Starting sFlow monitoring")
            logger.info("Creating sFlow monitoring instances in the ovs switches")
            run_script("set_ovs_sflow.sh", logger.info, logger.error)
            logger.info("Starting sflowtool to record monitoring data to: %s" % output_path)
            self.output_file = open(pj(output_path, self.csv_filename), 'a+')
            keys = ','.join(self.sflow_keys_to_monitor)
            self.sflowtool_proc = Popen([self.sflowtool_cmd, "-k", "-L", keys],
                                        stderr=STDOUT, stdout=self.output_file)
            if self.interfaces_filename:
                self.interfaces = self.get_interfaces(save_json_to=pj(output_path, self.interfaces_filename))
            else:
                self.interfaces = self.get_interfaces()
        else:
            logger.error("Monitoring is already running")

    def stop_monitoring_and_save(self, output_path, pandas_processing=True, delete_csv=True):
        if self.sflowtool_proc is not None:
            logger.info("Stopping sflowtool")
            self.sflowtool_proc.terminate()
            self.sflowtool_proc = None
            self.output_file.seek(0)
            samples_df = self.samples_processor(self.output_file,
                                                self.sflow_keys_to_monitor,
                                                self.interfaces,
                                                normalize_by=self.normalize_by)
            samples_df.to_hdf(pj(output_path, self.hd5_filename))
            self.interfaces = None
            self.output_file.close()
            if delete_csv:
                remove(self.output_file.name)
            self.output_file = None
            return samples_df
        else:
            logger.error("No monitoring running to stop")

    @staticmethod
    def get_samples_pandas(file, keys, interfaces, normalize_by=None):
        samples_df = pd.read_csv(file, names=keys, index_col=[0, 1])
        samples_df = samples_df.unstack()[keys[2]]
        interfaces_keys = {int(k) for k in interfaces.keys()}
        port_drop_list = list(filter(lambda k: k not in interfaces_keys, samples_df.keys()))
        samples_df.drop(columns=port_drop_list, inplace=True)
        samples_df.rename(lambda k: interfaces[str(k)], axis=1, inplace=True)
        samples_df.sort_index(axis=1, inplace=True)
        return samples_df if not normalize_by else samples_df / normalize_by

    @staticmethod
    def get_samples(file, keys, interfaces, normalize_by=None):
        samples = {}
        for line in file:
            # TODO: find a way to make this less brittle
            when, where, what = line.split(',')
            when = int(when)
            # use data only from the relevant interfaces
            if where in interfaces:
                where = interfaces[where]
                if normalize_by:
                    what = int(what) / float(normalize_by)
                else:
                    what = int(what)
                if when in samples:
                    samples[when][where] = what
                else:
                    samples[when] = {where: what}
        samples_df = pd.DataFrame.from_dict(samples, orient='index')
        samples_df.rename_axis(keys[0], inplace=True)
        samples_df.rename_axis(keys[1], axis=1, inplace=True)
        samples_df.sort_index(axis=1, inplace=True)
        return samples_df

    @staticmethod
    def get_interfaces(save_json_to=None):
        interfaces = get_inter_switch_port_interfaces()
        if save_json_to:
            with open(save_json_to, 'w') as f:
                dump(interfaces, f, sort_keys=True, indent=4)
        return interfaces
