#!/usr/bin/python

# GraphML-Topo-to-CSV
# This file parses Network Topologies in GraphML format from the Internet Topology Zoo.
# A CSV file describing the Topology will be created as Output.
#
#################################################################################
from xml.etree import ElementTree
import math
import argparse
import csv
from collections import namedtuple

Node = namedtuple('Node', 'Name, Latitude, Longitude')
Link = namedtuple('Link', 'From, To, Latency_in_ms')


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="The input file - a graphml topology file")
    parser.add_argument("-o", "--output", default="",
                        help="The output file - a CSV file based on the topology - To, From, Latency(ms)")
    args = parser.parse_args()
    if args.output == "":
        args.output = args.input + '.csv'
    return args


def get_graph_sets_from_xml(input_file, ns="{http://graphml.graphdrawing.org/xmlns}"):
    # READ FILE AND DO ALL THE ACTUAL PARSING IN THE NEXT PARTS
    xml_tree = ElementTree.parse(input_file)
    # GET ALL ELEMENTS THAT ARE PARENTS OF ELEMENTS NEEDED LATER ON
    root_element = xml_tree.getroot()
    graph_element = root_element.find(ns + 'graph')
    # GET ALL ELEMENT SETS NEEDED LATER ON
    index_values = root_element.findall(ns + 'key')
    nodes = graph_element.findall(ns + 'node')
    edges = graph_element.findall(ns + 'edge')
    return edges, nodes, index_values


def remove_bad_chars(text):
    bad_chars = "\\ `*_{}[]()>#+-.,!$?'"
    for c in bad_chars:
        if c in text:
            text = text.replace(c, "")
    return text


def get_dicts_from_node_set(nodes, index_values, ns="{http://graphml.graphdrawing.org/xmlns}"):
    # INITIALIZE VARIABLES TO SAVE FOUND DATA FIRST
    # for saving the current values
    node_name_value = ''
    node_longitude_value = ''
    node_latitude_value = ''

    id_node_map = {}
    # FIND OUT WHAT KEYS ARE TO BE USED, SINCE THIS DIFFERS IN DIFFERENT GRAPHML TOPOLOGIES
    node_label_name, node_latitude_name, node_longitude_name = \
        get_names_in_graphml(index_values)

    # NOW PARSE ELEMENT SETS TO GET THE DATA FOR THE TOPO
    # GET NODE_NAME DATA
    # GET LONGITUDE DATA
    # GET LATITUDE DATA
    for n in nodes:
        node_index_value = n.attrib['id']
        # get all data elements residing under all node elements
        data_set = n.findall(ns + 'data')
        # finally get all needed values
        for d in data_set:
            # node name
            if d.attrib['key'] == node_label_name:
                # strip all whitespace from names so they can be used as id's
                node_name_value = remove_bad_chars(d.text)
            # longitude data
            if d.attrib['key'] == node_longitude_name:
                node_longitude_value = d.text
            # latitude data
            if d.attrib['key'] == node_latitude_name:
                node_latitude_value = d.text
            id_node_map[node_index_value] = Node(node_name_value, node_longitude_value, node_latitude_value)
    return id_node_map


def get_names_in_graphml(index_values):
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


def calculate_latency(latitude_src_str, latitude_dst_str, longitude_src_str, longitude_dst_str):
    # CALCULATE DELAYS
    #    CALCULATION EXPLANATION
    #
    #    formula: (for distance)
    #    dist(SP,EP) = arccos{ sin(La[EP]) * sin(La[SP]) + cos(La[EP]) * cos(La[SP]) * cos(Lo[EP] - Lo[SP])} * r
    #    r = 6378.137 km
    #
    #    formula: (speed of light, not within a vacuumed box)
    #     v = 1.97 * 10**8 m/s
    #
    #    formula: (latency being calculated from distance and light speed)
    #    t = distance / speed of light
    #    t (in ms) = ( distance in km * 1000 (for meters) ) / ( speed of light / 1000 (for ms))
    #    ACTUAL CALCULATION: implementing this was no fun.
    latitude_src = math.radians(float(latitude_src_str))
    latitude_dst = math.radians(float(latitude_dst_str))
    longitude_src = math.radians(float(longitude_src_str))
    longitude_dst = math.radians(float(longitude_dst_str))
    first_product = math.sin(latitude_dst) * math.sin(latitude_src)
    second_product_first_part = math.cos(latitude_dst) * math.cos(latitude_src)
    second_product_second_part = math.cos(longitude_dst - longitude_src)
    distance = math.acos(first_product + (second_product_first_part * second_product_second_part)) * 6378.137
    # t (in ms) = ( distance in km * 1000 (for meters) ) / ( speed of light / 1000 (for ms))
    # t         = ( distance       * 1000              ) / ( 1.97 * 10**8   / 1000         )
    return (distance * 1000) / 197000


def get_switch_links(edges, nodes):
    switch_links = []
    for e in edges:
        # GET IDS FOR EASIER HANDLING
        src_id = e.attrib['source']
        dst_id = e.attrib['target']
        latency = calculate_latency(nodes[src_id].Latitude,
                                    nodes[dst_id].Latitude,
                                    nodes[src_id].Longitude,
                                    nodes[dst_id].Longitude)
        name_src = nodes[src_id].Name
        name_dst = nodes[dst_id].Name
        switch_links.append(Link(name_src, name_dst, latency))
    return switch_links


if __name__ == '__main__':
    args = parse_arguments()

    edge_set, node_set, index_values_set = get_graph_sets_from_xml(args.input)

    id_node_dict = get_dicts_from_node_set(node_set, index_values_set)

    links = get_switch_links(edge_set, id_node_dict)

    with open(args.output, 'w', newline='') as f:
        csv_writer = csv.DictWriter(f, Link._fields)
        csv_writer.writeheader()
        for link in links:
            csv_writer.writerow(link._asdict())

    print("Topology CSV generation SUCCESSFUL!")
