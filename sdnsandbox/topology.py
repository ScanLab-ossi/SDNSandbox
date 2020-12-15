from dataclasses import dataclass
from typing import Dict, List, Tuple
from urllib.request import urlopen
from mininet.topo import Topo
from xml.etree import ElementTree
import logging
from xml.etree.ElementTree import Element

from sdnsandbox.util import remove_bad_chars, calculate_geodesic_latency

logger = logging.getLogger(__name__)


@dataclass
class Switch:
    ID: int
    name: str


@dataclass
class Link:
    first_id: int
    second_id: int
    mininet_latency: str


@dataclass
class ITZSwitch(Switch):
    lat: float
    long: float


class TopologyFactory(object):
    @staticmethod
    def create(topology_conf):
        if topology_conf["type"] == "ITZ":
            with urlopen(topology_conf["graphml"]) as response:
                graphml = response.read().decode("utf-8")
                bandwidth = topology_conf["bandwidth"]
                return ITZTopologyFactory(graphml, bandwidth["host_mbps"], bandwidth["switch_mbps"]).create()
        else:
            raise ValueError("Unknown topology type=%s" % topology_conf["type"])


class SDNSandboxTopologyFactory(object):
    def __init__(self,
                 switches: Dict[int, Switch],
                 switch_links: List[Link],
                 host_bandwidth: int,
                 switch_bandwidth: int):
        self.switches = switches
        self.switch_links = switch_links
        self.host_bandwidth = host_bandwidth
        self.switch_bandwidth = switch_bandwidth

    def create(self) -> Topo:
        topo = Topo()
        for switch in self.switches.values():
            # create switch
            topo_switch_name = 's'+str(switch.ID)
            topo_switch = topo.addSwitch('s'+str(switch.ID))
            # create corresponding host
            host = topo.addHost(topo_switch_name+'-H')
            # link each switch and its host
            topo.addLink(topo_switch, host, bw=self.host_bandwidth)
        for link in self.switch_links:
            topo.addLink('s'+str(link.first_id), 's'+str(link.second_id),
                         bw=self.switch_bandwidth, delay=link.mininet_latency)
        return topo


class ITZTopologyFactory(SDNSandboxTopologyFactory):
    def __init__(self, graphml, host_bandwidth, switch_bandwidth):
        switches, switch_links = self.extract_switches_and_links_from_graphml(graphml)
        super().__init__(switches, switch_links, host_bandwidth, switch_bandwidth)

    @staticmethod
    def extract_switches_and_links_from_graphml(graphml) -> Tuple[Dict[int, ITZSwitch], List[Link]]:
        edge_set, node_set, index_values_set = ITZTopologyFactory.get_graph_sets_from_graphml(graphml)
        switches = ITZTopologyFactory.get_switches(node_set, index_values_set)
        links = ITZTopologyFactory.get_links(edge_set, switches)
        return switches, links

    @staticmethod
    def get_graph_sets_from_graphml(graphml, ns="{http://graphml.graphdrawing.org/xmlns}") \
            -> Tuple[List[Element], List[Element], List[Element]]:
        root_element = ElementTree.fromstring(graphml)
        graph_element = root_element.find(ns + 'graph')
        if graph_element:
            index_values = root_element.findall(ns + 'key')
            nodes = graph_element.findall(ns + 'node')
            edges = graph_element.findall(ns + 'edge')
            return edges, nodes, index_values
        else:
            raise RuntimeError("Missing graph element in graphml file")

    @staticmethod
    def get_switches(raw_nodes: List[Element],
                     index_values: List[Element],
                     ns="{http://graphml.graphdrawing.org/xmlns}")\
            -> Dict[int, ITZSwitch]:
        node_label_name, node_latitude_name, node_longitude_name = \
            ITZTopologyFactory.get_names_in_graphml(index_values)
        switches = {}
        for n in raw_nodes:
            node_name_value = ''
            node_longitude_value = ''
            node_latitude_value = ''
            node_index_value = int(n.attrib['id'])
            data_set = n.findall(ns + 'data')
            for d in data_set:
                if d.attrib['key'] == node_label_name:
                    # get rid of all bad characters from names so they can be used later without issues
                    node_name_value = remove_bad_chars(d.text, bad_chars="\\/ `*_{}[]()>#+-.,!$?'")
                if d.attrib['key'] == node_longitude_name and d.text:
                    node_longitude_value = d.text
                if d.attrib['key'] == node_latitude_name and d.text:
                    node_latitude_value = d.text
            if node_name_value == 'None':
                logger.debug("Found None as node name for index=%s - invalidating and skipping", node_index_value)
                continue
            if '' in [node_name_value, node_latitude_value, node_longitude_value]:
                logger.debug(
                    "Found empty string as node value (name/lat/long) for index=%s - invalidating and skipping",
                    node_index_value)
                continue
            switches[node_index_value] = ITZSwitch(ID=node_index_value,
                                                   name=node_name_value,
                                                   lat=float(node_latitude_value),
                                                   long=float(node_longitude_value))
            logger.debug("Added Switch=%s", switches[node_index_value])
        logger.info("Found a total of %d valid switches", len(switches))
        return switches

    @staticmethod
    def get_names_in_graphml(index_values):
        """Find out what keys are to be used, since this differs in different graphml topologies"""
        node_label_name_in_graphml = ""
        node_latitude_name_in_graphml = ""
        node_longitude_name_in_graphml = ""
        for i in index_values:
            if i.attrib['attr.name'] == 'label' and i.attrib['for'] == 'node':
                node_label_name_in_graphml = i.attrib['id']
            if i.attrib['attr.name'] == 'Longitude':
                node_longitude_name_in_graphml = i.attrib['id']
            if i.attrib['attr.name'] == 'Latitude':
                node_latitude_name_in_graphml = i.attrib['id']
        if node_label_name_in_graphml == "":
            raise RuntimeError("Bad GraphML - missing node name label")
        if node_latitude_name_in_graphml == "":
            raise RuntimeError("Bad GraphML - missing node latitude label")
        if node_longitude_name_in_graphml == "":
            raise RuntimeError("Bad GraphML - missing node longitude label")
        return node_label_name_in_graphml, node_latitude_name_in_graphml, node_longitude_name_in_graphml

    @staticmethod
    def get_links(edges: List[Element], switches: Dict[int, ITZSwitch], latency_function=calculate_geodesic_latency)\
            -> List[Link]:
        switch_links = []
        for e in edges:
            src_id = int(e.attrib.get('source', '-1'))
            dst_id = int(e.attrib.get('target', '-1'))
            src, dst = switches.get(src_id), switches.get(dst_id)
            if src is None or dst is None:
                logger.debug("Edge src/dst not in valid switch list - skipping Edge=%s", e.attrib)
                print("reject "+str(e.attrib))
                continue
            latency = latency_function(src.lat, src.long, dst.lat, dst.long)
            switch_links.append(Link(src.ID, dst.ID, '{:.6f}ms'.format(latency)))
        return switch_links
