import unittest

from sdnsandbox.link import Link
from sdnsandbox.topology import SDNSandboxTopologyFactory, ITZTopologyFactory
from os.path import join as pj, dirname, abspath


class TopologyTestCase(unittest.TestCase):
    def test_create(self):
        switch_ids = ['1', '2']
        switch_links = [Link('1', 'One', '2', 'Two', 1)]
        topo = SDNSandboxTopologyFactory(switch_ids, switch_links, 10, 100).create()
        # TODO: fix test when using a linux machine (can't import mininet on windows)
        self.assertEqual([], topo.switches())
        self.assertEqual([], topo.links())

    def test_extract_switches_and_links(self):
        aarnet_links = [
            Link(From_ID='0', From_Name='Sydney1', To_ID='10', To_Name='Canberra2', Latency_in_ms='1.1930416560811434'),
            Link(From_ID='0', From_Name='Sydney1', To_ID='3', To_Name='Sydney2', Latency_in_ms='0.0'),
            Link(From_ID='0', From_Name='Sydney1', To_ID='6', To_Name='Brisbane1', Latency_in_ms='3.5276717985913124'),
            Link(From_ID='1', From_Name='Brisbane2', To_ID='3', To_Name='Sydney2', Latency_in_ms='3.5276717985913124'),
            Link(From_ID='1', From_Name='Brisbane2', To_ID='6', To_Name='Brisbane1', Latency_in_ms='0.0'),
            Link(From_ID='2', From_Name='Canberra1', To_ID='10', To_Name='Canberra2', Latency_in_ms='0.0'),
            Link(From_ID='2', From_Name='Canberra1', To_ID='15', To_Name='Melbourne1', Latency_in_ms='2.25345012971434'),
            Link(From_ID='3', From_Name='Sydney2', To_ID='8', To_Name='Armidale', Latency_in_ms='1.8055532891327202'),
            Link(From_ID='3', From_Name='Sydney2', To_ID='16', To_Name='Melbourne2', Latency_in_ms='3.4464406627808724'),
            Link(From_ID='4', From_Name='Townsville', To_ID='5', To_Name='Cairns', Latency_in_ms='1.3541652897904295'),
            Link(From_ID='4', From_Name='Townsville', To_ID='7', To_Name='Rockhampton', Latency_in_ms='2.883700606133203'),
            Link(From_ID='6', From_Name='Brisbane1', To_ID='7', To_Name='Rockhampton', Latency_in_ms='2.506004297758198'),
            Link(From_ID='9', From_Name='Hobart', To_ID='16', To_Name='Melbourne2', Latency_in_ms='2.883661110026281'),
            Link(From_ID='9', From_Name='Hobart', To_ID='15', To_Name='Melbourne1', Latency_in_ms='2.883661110026281'),
            Link(From_ID='11', From_Name='Perth1', To_ID='12', To_Name='Perth2', Latency_in_ms='0.0'),
            Link(From_ID='11', From_Name='Perth1', To_ID='13', To_Name='Adelaide1', Latency_in_ms='10.32477688235756'),
            Link(From_ID='12', From_Name='Perth2', To_ID='14', To_Name='Adelaide2', Latency_in_ms='10.32477688235756'),
            Link(From_ID='13', From_Name='Adelaide1', To_ID='18', To_Name='Darwin', Latency_in_ms='12.598910927956187'),
            Link(From_ID='13', From_Name='Adelaide1', To_ID='14', To_Name='Adelaide2', Latency_in_ms='0.0'),
            Link(From_ID='13', From_Name='Adelaide1', To_ID='15', To_Name='Melbourne1', Latency_in_ms='3.1585880449026877'),
            Link(From_ID='14', From_Name='Adelaide2', To_ID='16', To_Name='Melbourne2', Latency_in_ms='3.1585880449026877'),
            Link(From_ID='14', From_Name='Adelaide2', To_ID='17', To_Name='AliceSprings', Latency_in_ms='6.403604933918101'),
            Link(From_ID='15', From_Name='Melbourne1', To_ID='16', To_Name='Melbourne2', Latency_in_ms='0.0'),
            Link(From_ID='17', From_Name='AliceSprings', To_ID='18', To_Name='Darwin', Latency_in_ms='6.203371526720749')]

        graphml_path = pj(dirname(abspath(__file__)),"Aarnet.graphml")
        with open(graphml_path) as f:
            graphml = f.read()
            switch_ids, switch_links = ITZTopologyFactory.extract_switches_and_links_from_graphml(graphml)
            self.assertEqual([str(sw_id) for sw_id in range(19)], list(switch_ids))
            self.assertEqual(aarnet_links, switch_links)



if __name__ == '__main__':
    unittest.main()
