import unittest

from sdnsandbox.topology import SDNSandboxTopologyFactory, ITZTopologyFactory, Link, Switch
from os.path import join as pj, dirname, abspath


class TopologyTestCase(unittest.TestCase):
    def test_create(self):
        switches = {1: Switch(1, '1'), 2: Switch(2, '2')}
        switch_links = [Link(1, 2, '1ms')]
        topo = SDNSandboxTopologyFactory(switches, switch_links, 10, 100).create()
        self.assertEqual(['s1', 's2'], topo.switches())
        self.assertEqual([('s1', 's1-H'), ('s1', 's2'), ('s2', 's2-H')], topo.links())

    def test_extract_switches_and_links(self):
        aarnet_links = [
            Link(first_id=0, second_id=10, mininet_latency='1.193042ms'),
            Link(first_id=0, second_id=3, mininet_latency='0.000000ms'),
            Link(first_id=0, second_id=6, mininet_latency='3.527672ms'),
            Link(first_id=1, second_id=3, mininet_latency='3.527672ms'),
            Link(first_id=1, second_id=6, mininet_latency='0.000000ms'),
            Link(first_id=2, second_id=10, mininet_latency='0.000000ms'),
            Link(first_id=2, second_id=15, mininet_latency='2.253450ms'),
            Link(first_id=3, second_id=8, mininet_latency='1.805553ms'),
            Link(first_id=3, second_id=16, mininet_latency='3.446441ms'),
            Link(first_id=4, second_id=5, mininet_latency='1.354165ms'),
            Link(first_id=4, second_id=7, mininet_latency='2.883701ms'),
            Link(first_id=6, second_id=7, mininet_latency='2.506004ms'),
            Link(first_id=9, second_id=16,mininet_latency='2.883661ms'),
            Link(first_id=9, second_id=15, mininet_latency='2.883661ms'),
            Link(first_id=11, second_id=12, mininet_latency='0.000000ms'),
            Link(first_id=11, second_id=13, mininet_latency='10.324777ms'),
            Link(first_id=12, second_id=14, mininet_latency='10.324777ms'),
            Link(first_id=13, second_id=18, mininet_latency='12.598911ms'),
            Link(first_id=13, second_id=14, mininet_latency='0.000000ms'),
            Link(first_id=13, second_id=15, mininet_latency='3.158588ms'),
            Link(first_id=14, second_id=16, mininet_latency='3.158588ms'),
            Link(first_id=14, second_id=17, mininet_latency='6.403605ms'),
            Link(first_id=15, second_id=16, mininet_latency='0.000000ms'),
            Link(first_id=17, second_id=18, mininet_latency='6.203372ms')]

        graphml_path = pj(dirname(abspath(__file__)), "Aarnet.graphml")
        with open(graphml_path) as f:
            graphml = f.read()
            switches, switch_links = ITZTopologyFactory.extract_switches_and_links_from_graphml(graphml)
            self.assertEqual([sw_id for sw_id in range(19)], list(switches.keys()))
            self.assertEqual(aarnet_links, switch_links)


if __name__ == '__main__':
    unittest.main()
