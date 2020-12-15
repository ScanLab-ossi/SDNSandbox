import pathlib
from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from json import dump

import dacite
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
            config = dacite.from_dict(data_class=SFlowConfig, data=monitor_conf)
            return SFlowMonitor(config)
        else:
            raise ValueError("Unknown monitor type=%s" % monitor_conf["type"])


class Monitor(ABC):
    @abstractmethod
    def start_monitoring(self, output_path):
        pass

    @abstractmethod
    def stop_monitoring_and_save(self, output_path):
        pass


@dataclass
class SFlowConfig:
    data_key: str
    normalize_by: float
    csv_filename: str = 'sflow.csv'
    interfaces_filename: str = 'interfaces.json'
    hd5_filename: str = 'sflow.hd5'
    pandas_processing: bool = True
    sflowtool_cmd: str = "sflowtool"


class SFlowMonitor(Monitor):
    """A Monitor using an sFlow collector process and OvS-embedded sFlow monitoring"""
    sflow_time_key = "unixSecondsUTC"
    sflow_intf_index_key = "ifIndex"
    hd5_key = "sdnsandbox_data"

    def __init__(self, config: SFlowConfig):
        if which(config.sflowtool_cmd) is None:
            raise RuntimeError("command %s is not available, can't setup sFlow monitoring" % config.sflowtool_cmd)
        self.sflow_keys_to_monitor = [self.sflow_time_key, self.sflow_intf_index_key, config.data_key]
        self.config = config
        self.sflowtool_proc = None
        self.output_file = None
        self.interfaces = None
        self.samples_processor = self.get_samples_pandas if config.pandas_processing else self.get_samples

    def start_monitoring(self, output_path):
        if self.sflowtool_proc is None:
            logger.info("Starting sFlow monitoring")
            logger.info("Creating sFlow monitoring instances in the ovs switches")
            run_script("set_ovs_sflow.sh", logger.info, logger.error)
            logger.info("Starting %s to record monitoring data to: %s" % (self.config.sflowtool_cmd, output_path))
            self.output_file = open(pj(output_path, self.config.csv_filename), 'a+')
            keys = ','.join(self.sflow_keys_to_monitor)
            self.sflowtool_proc = Popen([self.config.sflowtool_cmd, "-k", "-L", keys],
                                        stderr=STDOUT, stdout=self.output_file)
            self.interfaces = self.get_interfaces(save_json_to=pj(output_path, self.config.interfaces_filename))

        else:
            logger.error("Monitoring is already running")

    def stop_monitoring_and_save(self, output_path, pandas_processing=True, delete_csv=True):
        if self.sflowtool_proc is not None:
            logger.info("Stopping %s", self.config.sflowtool_cmd)
            self.sflowtool_proc.terminate()
            self.sflowtool_proc = None
            logger.info("Processing sFlow samples...")
            self.output_file.seek(0)
            samples_df = self.samples_processor(self.output_file,
                                                self.sflow_keys_to_monitor,
                                                self.interfaces,
                                                normalize_by=self.config.normalize_by)
            logger.info("Saving samples as %s", self.config.hd5_filename)
            samples_df.to_hdf(pj(output_path, self.config.hd5_filename), key=self.hd5_key)
            self.interfaces = None
            self.output_file.close()
            if delete_csv:
                logger.info("Deleting original sFlow CSV %s", self.output_file.name)
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
