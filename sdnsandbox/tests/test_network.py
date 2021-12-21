from dataclasses import asdict
from json import dumps
from unittest import TestCase

from mininet.node import Controller

from sdnsandbox.network import SDNSandboxNetwork, Interface, SDNSandboxNetworkConfig
from sdnsandbox.topology import SDNSandboxTopologyCreator, Switch, Link


class TestNetwork(TestCase):
    ip_a_output = '''
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: s0-eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc htb master ovs-system state UP group default qlen 1000
    link/ether 16:47:ba:01:0b:05 brd ff:ff:ff:ff:ff:ff link-netnsid 1
3: s3-eth2@s0-eth3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc htb master ovs-system state UP group default qlen 1000
    link/ether 86:57:62:6c:06:1b brd ff:ff:ff:ff:ff:ff
    '''
    expected_net_data_dict = {
    "interfaces": {
        13: {
            "name": "name13",
            "net_meaning": "mean13",
            "num": 13
        },
        15: {
            "name": "name15",
            "net_meaning": "mean15",
            "num": 15
        }
    },
    "switch_links": [
        {
            "first_id": 13,
            "mininet_latency": "1.234567ms",
            "second_id": 15
        }
    ],
    "switches": {
        13: {
            "ID": 13,
            "name": "name13"
        },
        15: {
            "ID": 15,
            "name": "name15"
        }
    }
}
    switch_num_to_name = {0: 'zero', 3: 'three'}
    relevant_interfaces = {3: Interface(3, 's3-eth2@s0-eth3', 'three-eth2@zero-eth3')}

    def test_get_network_data(self):
        switches = {13: Switch(13, 'name13'), 15: Switch(15, 'name15')}
        switch_links = [Link(13, 15, '1.234567ms')]
        topology_creator_mock = SDNSandboxTopologyCreator(switches, switch_links, 0, 0)
        controller = Controller('controller')
        mock_config = SDNSandboxNetworkConfig(topology_creator_mock, controller)
        net = SDNSandboxNetwork(mock_config)
        # override start check
        net.net = True
        net.interfaces = {13: Interface(13, 'name13', 'mean13'), 15: Interface(15, 'name15', 'mean15')}
        network_data = net.get_network_data()
        self.assertEqual(self.expected_net_data_dict, asdict(network_data))

    def test_get_interface_net_meaning(self):
        net_meaning = SDNSandboxNetwork.get_interface_net_meaning('s3-eth2@s0-eth3', self.switch_num_to_name)
        self.assertEqual(self.relevant_interfaces[3].net_meaning, net_meaning)

    def test_get_inter_switch_port_interfaces(self):
        interfaces = SDNSandboxNetwork.get_inter_switch_port_interfaces(self.switch_num_to_name,
                                                                        ip_a_getter=lambda: self.ip_a_output)
        self.assertEqual(self.relevant_interfaces, interfaces)
