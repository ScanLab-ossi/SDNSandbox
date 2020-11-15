from urllib.request import urlopen
from mininet.topo import Topo
from collections import namedtuple
from sdnsandbox.link import Link
from xml.etree import ElementTree
import logging
from sdnsandbox.util import remove_bad_chars, calculate_geodesic_latency

Node = namedtuple('Node', 'Name, Latitude, Longitude')


logger = logging.getLogger(__name__)


class TopologyFactory(object):
    @staticmethod
    def create(topology_conf):
        if topology_conf["type"] == "ITZ":
            with urlopen(topology_conf["graphml"]) as response:
                graphml = response.read().decode("utf-8")
                bandwidth = topology_conf["bandwidth"]
                return ITZTopologyBuilder(graphml, bandwidth["host_mbps"], bandwidth["switch_mbps"]).build()
        else:
            raise ValueError("Unknown topology type=%s" % topology_conf["type"])


class SDNSandboxTopologyBuilder(object):
    def __init__(self, switch_ids, switch_links, host_bandwidth, switch_bandwidth):
        self.switch_ids = switch_ids
        self.switch_links = switch_links
        self.host_bandwidth = host_bandwidth
        self.switch_bandwidth = switch_bandwidth

    def build(self):
        topo = Topo()
        for switch_id in self.switch_ids:
            # create switch
            switch_name = 's'+switch_id
            switch = topo.addSwitch(switch_name)
            # create corresponding host
            host = topo.addHost(switch_name+'-H')
            # link each switch and its host
            topo.addLink(switch, host, bw=self.host_bandwidth)
        for link in self.switch_links:
            topo.addLink('s'+link.From_ID, 's'+link.To_ID, bw=self.switch_bandwidth, delay=link.Latency_in_ms+'ms')
        return topo


class ITZTopologyBuilder(SDNSandboxTopologyBuilder):
    def __init__(self, graphml, host_bandwidth, switch_bandwidth):
        self.graphml = graphml
        self.host_bandwidth = host_bandwidth
        self.switch_bandwidth = switch_bandwidth

    def build(self):
        edge_set, node_set, index_values_set = self.get_graph_sets_from_graphml(self.graphml)
        id_node_dict = self.get_id_node_map(node_set, index_values_set)
        switch_links = self.get_switch_links(edge_set, id_node_dict)
        super().__init__(id_node_dict.keys(), switch_links, self.host_bandwidth, self.switch_bandwidth)
        return super().build()

    @staticmethod
    def get_graph_sets_from_graphml(graphml, ns="{http://graphml.graphdrawing.org/xmlns}"):
        root_element = ElementTree.fromstring(graphml)
        graph_element = root_element.find(ns + 'graph')
        index_values = root_element.findall(ns + 'key')
        nodes = graph_element.findall(ns + 'node')
        edges = graph_element.findall(ns + 'edge')
        return edges, nodes, index_values

    @staticmethod
    def get_id_node_map(nodes, index_values, ns="{http://graphml.graphdrawing.org/xmlns}"):
        node_label_name, node_latitude_name, node_longitude_name = \
            ITZTopologyBuilder.get_names_in_graphml(index_values)
        id_node_map = {}
        for n in nodes:
            node_name_value = ''
            node_longitude_value = ''
            node_latitude_value = ''
            node_index_value = n.attrib['id']
            data_set = n.findall(ns + 'data')
            for d in data_set:
                if d.attrib['key'] == node_label_name:
                    # get rid of all bad characters from names so they can be used later without issues
                    node_name_value = remove_bad_chars(d.text, bad_chars="\\/ `*_{}[]()>#+-.,!$?'")
                if d.attrib['key'] == node_longitude_name:
                    node_longitude_value = d.text
                if d.attrib['key'] == node_latitude_name:
                    node_latitude_value = d.text
            if node_name_value == 'None':
                logger.debug("Found None as node name for index=%s - invalidating and skipping", node_index_value)
                continue
            if '' in [node_name_value, node_latitude_value, node_longitude_value]:
                logger.debug(
                    "Found empty string as node value (name/lat/long) for index=%s - invalidating and skipping",
                    node_index_value)
                continue
            id_node_map[node_index_value] = Node(node_name_value, node_latitude_value, node_longitude_value)
            logger.debug("Added for key=%s Node=%s", node_index_value, id_node_map[node_index_value])
        logger.info("Found a total of %d valid nodes", len(id_node_map))
        return id_node_map

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
    def get_switch_links(edges, nodes, latency_function=calculate_geodesic_latency):
        switch_links = []
        for e in edges:
            # GET IDS FOR EASIER HANDLING
            src_id = e.attrib['source']
            dst_id = e.attrib['target']
            if not {src_id, dst_id}.issubset(nodes.keys()):
                logger.debug("Missing edge node id in valid node list - skipping Edge=%s", e.attrib)
                continue
            latency = latency_function(float(nodes[src_id].Latitude),
                                       float(nodes[src_id].Longitude),
                                       float(nodes[dst_id].Latitude),
                                       float(nodes[dst_id].Longitude))
            src_name = nodes[src_id].Name
            dst_name = nodes[dst_id].Name
            switch_links.append(Link(src_id, src_name, dst_id, dst_name, str(latency)))
        return switch_links
