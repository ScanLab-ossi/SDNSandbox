import unittest

from sdnsandbox.link import Link
from sdnsandbox.topology import SDNSandboxTopologyFactory, ITZTopologyFactory
from os.path import join as pj, dirname, abspath


class TopologyTestCase(unittest.TestCase):
    def test_create(self):
        switch_ids = ['1', '2']
        switch_links = [Link('1', 'One', '2', 'Two', '1')]
        topo = SDNSandboxTopologyFactory(switch_ids, switch_links, 10, 100).create()
        self.assertEqual(['s1', 's2'], topo.switches())
        self.assertEqual([('s1', 's1-H'), ('s1', 's2'), ('s2', 's2-H')], topo.links())

    def test_extract_switches_and_links(self):
        aarnet_links = [
            Link(From_ID='0', From_Name='Sydney1', To_ID='10', To_Name='Canberra2', Latency_in_ms='1.193042'),
            Link(From_ID='0', From_Name='Sydney1', To_ID='3', To_Name='Sydney2', Latency_in_ms='0.000000'),
            Link(From_ID='0', From_Name='Sydney1', To_ID='6', To_Name='Brisbane1', Latency_in_ms='3.527672'),
            Link(From_ID='1', From_Name='Brisbane2', To_ID='3', To_Name='Sydney2', Latency_in_ms='3.527672'),
            Link(From_ID='1', From_Name='Brisbane2', To_ID='6', To_Name='Brisbane1', Latency_in_ms='0.000000'),
            Link(From_ID='2', From_Name='Canberra1', To_ID='10', To_Name='Canberra2', Latency_in_ms='0.000000'),
            Link(From_ID='2', From_Name='Canberra1', To_ID='15', To_Name='Melbourne1', Latency_in_ms='2.253450'),
            Link(From_ID='3', From_Name='Sydney2', To_ID='8', To_Name='Armidale', Latency_in_ms='1.805553'),
            Link(From_ID='3', From_Name='Sydney2', To_ID='16', To_Name='Melbourne2', Latency_in_ms='3.446441'),
            Link(From_ID='4', From_Name='Townsville', To_ID='5', To_Name='Cairns', Latency_in_ms='1.354165'),
            Link(From_ID='4', From_Name='Townsville', To_ID='7', To_Name='Rockhampton', Latency_in_ms='2.883701'),
            Link(From_ID='6', From_Name='Brisbane1', To_ID='7', To_Name='Rockhampton', Latency_in_ms='2.506004'),
            Link(From_ID='9', From_Name='Hobart', To_ID='16', To_Name='Melbourne2', Latency_in_ms='2.883661'),
            Link(From_ID='9', From_Name='Hobart', To_ID='15', To_Name='Melbourne1', Latency_in_ms='2.883661'),
            Link(From_ID='11', From_Name='Perth1', To_ID='12', To_Name='Perth2', Latency_in_ms='0.000000'),
            Link(From_ID='11', From_Name='Perth1', To_ID='13', To_Name='Adelaide1', Latency_in_ms='10.324777'),
            Link(From_ID='12', From_Name='Perth2', To_ID='14', To_Name='Adelaide2', Latency_in_ms='10.324777'),
            Link(From_ID='13', From_Name='Adelaide1', To_ID='18', To_Name='Darwin', Latency_in_ms='12.598911'),
            Link(From_ID='13', From_Name='Adelaide1', To_ID='14', To_Name='Adelaide2', Latency_in_ms='0.000000'),
            Link(From_ID='13', From_Name='Adelaide1', To_ID='15', To_Name='Melbourne1', Latency_in_ms='3.158588'),
            Link(From_ID='14', From_Name='Adelaide2', To_ID='16', To_Name='Melbourne2', Latency_in_ms='3.158588'),
            Link(From_ID='14', From_Name='Adelaide2', To_ID='17', To_Name='AliceSprings', Latency_in_ms='6.403605'),
            Link(From_ID='15', From_Name='Melbourne1', To_ID='16', To_Name='Melbourne2', Latency_in_ms='0.000000'),
            Link(From_ID='17', From_Name='AliceSprings', To_ID='18', To_Name='Darwin', Latency_in_ms='6.203372')]

        graphml_path = pj(dirname(abspath(__file__)),"Aarnet.graphml")
        with open(graphml_path) as f:
            graphml = f.read()
            switch_ids, switch_links = ITZTopologyFactory.extract_switches_and_links_from_graphml(graphml)
            self.assertEqual([str(sw_id) for sw_id in range(19)], list(switch_ids))
            self.assertEqual(aarnet_links, switch_links)



if __name__ == '__main__':
    unittest.main()
