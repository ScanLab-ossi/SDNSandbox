from abc import ABC, abstractmethod
import logging
from dataclasses import dataclass
from typing import Dict, Optional

import dacite
import pandas as pd

from sdnsandbox.util import run_script
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
    def start_monitoring(self, output_path: str):
        pass

    @abstractmethod
    def process_monitoring_data(self, interfaces_naming: Dict[int, str]) -> Optional[pd.DataFrame]:
        pass


@dataclass
class SFlowConfig:
    data_key: str
    normalize_by: float
    is_cumulative_data: bool = True
    csv_filename: str = 'sflow.csv'
    pandas_processing: bool = True
    sflowtool_cmd: str = "sflowtool"
    delete_csv: bool = True


class SFlowMonitor(Monitor):
    """A Monitor using an sFlow collector process and OvS-embedded sFlow monitoring"""
    sflow_time_key = "unixSecondsUTC"
    sflow_intf_index_key = "ifIndex"

    def __init__(self, config: SFlowConfig):
        if which(config.sflowtool_cmd) is None:
            raise RuntimeError("command %s is not available, can't setup sFlow monitoring" % config.sflowtool_cmd)
        self.sflow_keys_to_monitor = [self.sflow_time_key, self.sflow_intf_index_key, config.data_key]
        self.config = config
        self.sflowtool_proc = None
        self.output_file = None
        self.samples_processor = self.get_samples_pandas if config.pandas_processing else self.get_samples

    def start_monitoring(self, output_path):
        if self.sflowtool_proc is None:
            logger.info("Starting sFlow monitoring")
            logger.info("Creating sFlow monitoring instances in the ovs switches")
            run_script("set_ovs_sflow.sh", logger.info, logger.error)
            self.output_file = open(pj(output_path, self.config.csv_filename), 'a+')
            logger.info("Starting %s to record monitoring data to: %s" % (self.config.sflowtool_cmd,
                                                                          self.output_file.name))
            keys = ','.join(self.sflow_keys_to_monitor)
            self.sflowtool_proc = Popen([self.config.sflowtool_cmd, "-k", "-L", keys],
                                        stderr=STDOUT, stdout=self.output_file)
        else:
            logger.error("Monitoring is already running")

    def process_monitoring_data(self, interfaces_naming: Dict[int, str]) -> Optional[pd.DataFrame]:
        if self.sflowtool_proc is not None:
            logger.info("Stopping %s", self.config.sflowtool_cmd)
            self.sflowtool_proc.terminate()
            self.sflowtool_proc = None
            logger.info("Processing sFlow samples...")
            self.output_file.seek(0)
            samples_df = self.samples_processor(self.output_file,
                                                self.sflow_keys_to_monitor,
                                                interfaces_naming,
                                                is_cumulative_data=self.config.is_cumulative_data,
                                                normalize_by=self.config.normalize_by)
            self.output_file.close()
            if self.config.delete_csv:
                logger.info("Deleting original sFlow CSV %s", self.output_file.name)
                remove(self.output_file.name)
            self.output_file = None
            return samples_df
        else:
            logger.error("No monitoring currently running to stop and process")
            return None

    @staticmethod
    def get_samples_pandas(file, keys, interfaces_naming: Dict[int, str], is_cumulative_data=True, normalize_by=None):
        samples_df = pd.read_csv(file, names=keys, index_col=[0, 1])
        samples_df = samples_df.unstack()[keys[2]]
        if is_cumulative_data:
            # subtract the previous row (the data is cumulative) and remove the first row which is now NaN
            samples_df = samples_df.diff().iloc[1:]
        interfaces_keys = set(interfaces_naming.keys())
        port_drop_list = list(filter(lambda k: k not in interfaces_keys, samples_df.keys()))
        samples_df.drop(columns=port_drop_list, inplace=True)
        # sort first to not be influenced by the renaming
        samples_df.sort_index(axis=1, inplace=True)
        samples_df.rename(lambda k: interfaces_naming[k], axis=1, inplace=True)
        return samples_df / 1.0 if not normalize_by else samples_df / normalize_by

    @staticmethod
    def get_samples(file, keys, interfaces_naming: Dict[int, str], is_cumulative_data=True, normalize_by=None):
        samples: Dict[int, Dict[str, float]] = {}
        for line in file:
            when, where, what = line.split(',')
            when = int(when)
            where = int(where)
            # use data only from the relevant interfaces
            if where in interfaces_naming:
                if normalize_by:
                    what = int(what) / float(normalize_by)
                else:
                    what = float(what)
                if when in samples:
                    samples[when][where] = what
                else:
                    samples[when] = {where: what}
        samples_df = pd.DataFrame.from_dict(samples, orient='index')
        if is_cumulative_data:
            # subtract the previous row (the data is cumulative) and remove the first row which is now NaN
            samples_df = samples_df.diff().iloc[1:]
        samples_df.rename_axis(keys[0], inplace=True)
        samples_df.rename_axis(keys[1], axis=1, inplace=True)
        samples_df.sort_index(axis=1, inplace=True)
        return samples_df
