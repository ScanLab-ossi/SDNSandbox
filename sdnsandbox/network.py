import logging
from dataclasses import asdict, dataclass
from subprocess import run, PIPE
from typing import List, Dict

import dacite
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import Host, Controller, RemoteController
from mininet.util import dumpNetConnections
from socket import gethostbyname_ex
from sdnsandbox.topology import SDNSandboxTopologyCreator, TopologyCreatorFactory, Link, Switch
from sdnsandbox.util import countdown
from re import fullmatch

logger = logging.getLogger(__name__)


class SDNSandboxNetworkFactory(object):
    @staticmethod
    def create(network_conf):
        # we assume the first ip is enough, this works for both an IP address and DNS name
        controller_ip = gethostbyname_ex(network_conf['controller']['ip'])[2][0]
        controller = RemoteController('controller', ip=controller_ip, port=network_conf['controller']['port'])
        network_conf['controller'] = controller
        topology_creator = TopologyCreatorFactory.create(network_conf['topology_creator'])
        network_conf['topology_creator'] = topology_creator
        config = dacite.from_dict(data_class=SDNSandboxNetworkConfig, data=network_conf)
        return SDNSandboxNetwork(config)


@dataclass
class Interface:
    num: int
    name: str
    net_meaning: str


@dataclass
class SDNSandboxNetworkConfig:
    topology_creator: SDNSandboxTopologyCreator
    controller: Controller
    test_ping_all_full: bool = False


@dataclass
class SDNSandboxNetworkData:
    interfaces: Dict[int, Interface]
    switches: Dict[int, Switch]
    switch_links: List[Link]


class SDNSandboxNetwork:
    def __init__(self, config: SDNSandboxNetworkConfig):
        self.config = config
        self.interfaces: Dict[int, Interface] = {}
        self.net = None

    def start(self):
        """Create network and start it"""
        topology = config.topology_creator.create()
        self.net = Mininet(topo=topology, controller=lambda unneeded: config.controller, link=TCLink)
        self.net.start()

        logger.info("Waiting for the controller to finish network setup...")
        countdown(logger.info, 3)

        dumpNetConnections(self.net)
        if self.config.test_ping_all_full:
            logger.info("Performing a full mesh ping to make sure the network is well connected...")
            self.net.pingAllFull()
        switch_names = {sw.ID: sw.name for sw in self.config.topology_creator.switches.values()}
        self.interfaces = self.get_inter_switch_port_interfaces(switch_names)
        return self.net

    def stop(self):
        if self.net==None: raise RuntimeError("Can't run this when the network is not started first!")
        logger.info("Stopping the network...")
        self.net.stop()
        self.net = None
        self.interfaces = {}

    def get_hosts(self) -> List[Host]:
        if self.net==None: raise RuntimeError("Can't run this when the network is not started first!")
        return self.net.hosts

    @staticmethod
    def get_interface_net_meaning(intf_name: str, switches: Dict[int, str]):
        split = intf_name.split('@')
        for switch in split:
            switch_name = switch.split('-')[0]
            switch_num = int(switch_name[1:])
            intf_name = intf_name.replace(switch_name + '-', switches[switch_num] + '-')
        return intf_name

    @staticmethod
    def get_inter_switch_port_interfaces(switches: Dict[int, str],
                                         port_re="s[0-9]+-eth[0-9]+@s[0-9]+-eth[0-9]+",
                                         ip_a_getter=lambda:
                                         run(["ip", "a"], universal_newlines=True, stdout=PIPE, stderr=PIPE).stdout) \
            -> Dict[int, Interface]:
        ip_a_out = ip_a_getter()
        interfaces = {}
        for line in ip_a_out.splitlines():
            # ignore none-main lines (those with extra data, not intf definition)
            if len(line) == 0 or line[0] == ' ':
                continue
            intf_split = line.split(':')
            intf_num = int(intf_split[0])
            intf_name = intf_split[1].strip()
            logger.debug("found interface #%d: \n%s", intf_num, intf_name)
            if fullmatch(port_re, intf_name):
                interfaces[intf_num] = Interface(intf_num,
                                                 intf_name,
                                                 SDNSandboxNetwork.get_interface_net_meaning(intf_name, switches))
            else:
                logger.debug("Interface %s doesn't have inter switch port name, irrelevant - dropped...", intf_name)
        return interfaces

    def get_interfaces(self) -> Dict[int, Interface]:
        if self.net==None: raise RuntimeError("Can't run this when the network is not started first!")
        return self.interfaces

    def get_network_data(self) -> SDNSandboxNetworkData:
        if self.net==None: raise RuntimeError("Can't run this when the network is not started first!")
        return SDNSandboxNetworkData(self.interfaces,
                                     self.config.topology_creator.switches,
                                     self.config.topology_creator.switch_links)
