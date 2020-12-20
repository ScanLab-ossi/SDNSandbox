import logging
from dataclasses import dataclass, asdict
from enum import Enum
from json import dump, load
from os import makedirs
from typing import Dict, Callable
from os.path import join as pj
from dacite import from_dict

from sdnsandbox.load_generator import LoadGenerator, LoadGeneratorFactory
from sdnsandbox.monitor import Monitor, MonitorFactory
from sdnsandbox.network import SDNSandboxNetwork, Interface, SDNSandboxNetworkFactory

logger = logging.getLogger(__name__)


class RunnerFactory:
    @staticmethod
    def create(config_path: str, output_dir: str, logs_dir: str):
        with open(config_path) as conf_file:
            conf = load(conf_file)['runner']
            conf['load_generator'] = LoadGeneratorFactory.create(conf['load_generator'])
            conf['monitor'] = MonitorFactory.create(conf['monitor'])
            conf['network'] = SDNSandboxNetworkFactory.create(conf['network'])
            conf['output_dir'] = output_dir
            conf['logs_dir'] = logs_dir
            data = from_dict(RunnerData, conf)
            return Runner(data)


class InterfaceTranslation(Enum):
    NUM_TO_STRING = 0
    TRANSLATE_TO_NAMES = 1
    TRANSLATE_TO_MEANINGS = 2


@dataclass
class RunnerData:
    network: SDNSandboxNetwork
    load_generator: LoadGenerator
    monitor: Monitor
    output_dir: str
    logs_dir: str
    network_data_filename: str = 'network_data.json'
    hd5_key: str = 'sdnsandbox_data'
    hd5_filename: str = 'sdnsandbox.hd5'
    interfaces_translation: InterfaceTranslation = InterfaceTranslation.TRANSLATE_TO_MEANINGS


class Runner(object):
    def __init__(self, data: RunnerData):
        self.data = data

    def run(self):
        self.data.network.start()
        hosts = self.data.network.get_hosts()
        receivers_logs_path = pj(self.data.logs_dir, "receivers")
        makedirs(receivers_logs_path)
        self.data.load_generator.start_receivers(hosts, self.data.output_dir, logs_path=receivers_logs_path)
        self.data.monitor.start_monitoring(self.data.output_dir)
        senders_logs_path = pj(self.data.logs_dir, "senders")
        makedirs(senders_logs_path)
        self.data.load_generator.run_senders(hosts, self.data.output_dir, logs_path=senders_logs_path)

    def stop_and_save(self):
        network_data = self.data.network.get_network_data()
        logger.info("Saving network data as %s", self.data.network_data_filename)
        with open(pj(self.data.output_dir, self.data.network_data_filename), 'w') as json_file:
            dump(asdict(network_data), json_file, sort_keys=True, indent=4)
        interfaces_naming = self.get_interfaces_naming(network_data.interfaces)
        monitoring_data_df = self.data.monitor.process_monitoring_data(interfaces_naming)
        logger.info("Saving samples as %s", self.data.hd5_filename)
        monitoring_data_df.to_hdf(pj(self.data.output_dir, self.data.hd5_filename), key=self.data.hd5_key)
        self.data.load_generator.stop_receivers()
        self.data.network.stop()

    def get_interfaces_naming(self, interfaces: Dict[int, Interface]) -> Dict[int, str]:
        getters: Dict[InterfaceTranslation, Callable[[Interface], str]] =\
            {InterfaceTranslation.NUM_TO_STRING: lambda i: i.num,
             InterfaceTranslation.TRANSLATE_TO_NAMES: lambda i: i.name,
             InterfaceTranslation.TRANSLATE_TO_MEANINGS: lambda i: i.net_meaning}
        return {num: getters[self.data.interfaces_translation](interfaces[num]) for num in interfaces.keys()}
