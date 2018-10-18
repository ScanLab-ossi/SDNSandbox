#!/usr/bin/python

#GraphML-Topo-to-Mininet-Network-Generator
# This file is based on a tool from the assesing-mininet project on github.com

# This file parses Network Topologies in GraphML format from the Internet Topology Zoo.
# A python file for creating Mininet Topologies will be created as Output.
#
#################################################################################
import os
from xml.etree import ElementTree
import math
import argparse

output_code = r'''#!/usr/bin/python

"""
Custom topology for Mininet, generated by GraphML-Topo-to-Mininet-Network-Generator.
"""
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Node
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.util import dumpNodeConnections
from subprocess import call
from os.path import expanduser
import time

class GeneratedTopo( Topo ):
    "Internet Topology Zoo Specimen."

    def __init__( self, **opts ):
        "Create a topology."

        # Initialize Topology
        Topo.__init__( self, **opts )

        # add switches, hosts and edges between switch and corresponding host...
{0}

        # add edges between switches
{1}

topos = {{ 'generated': ( lambda: GeneratedTopo() ) }}

# HERE THE CODE DEFINITION OF THE TOPOLOGY ENDS

# the following code produces an executable script working with a remote controller
# and providing ssh access to the the mininet hosts


def setupNetwork(controller_ip):
    "Create network and run simple performance test"
    topo = GeneratedTopo()
    net = Mininet(topo=topo, controller=lambda a: RemoteController( a, ip=controller_ip, port=6653 ), link=TCLink)
    # check if switches connected to controller
    if not net.waitConnected(timeout=10,delay=1):
        print "Controller appears to have not connect to switches!"
        #exit(1)
    # adds root for ssh + starts net
    connectToRootNS(net)
    return net

def connectToRootNS( network, ip='10.123.123.1', prefixLen=8, routes=['10.0.0.0/8'] ):
    "Connect hosts to root namespace via switch. Starts network."
    "network: Mininet() network object"
    "ip: IP address for root namespace node"
    "prefixLen: IP address prefix length (e.g. 8, 16, 24)"
    "routes: host networks to route to"
    switch = network.switches[0]
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    intf = TCLink( root, switch ).intf1
    root.setIP( ip, prefixLen, intf )
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )


def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timeformat = '{{:02d}}:{{:02d}}'.format(mins, secs)
        print(timeformat)
        time.sleep(1)
        t -= 1
    print('Done!')


def setupITG( network ):
    for host in network.hosts:
        host.cmd( '/usr/sbin/sshd -D &')
        host.cmd( '~/scripts/ITGRecv.sh &' )

    # DEBUGGING INFO
    print
    print "Dumping network links"
    dumpNodeConnections(network.hosts)
    dumpNodeConnections(network.switches)
    dumpNodeConnections(network.controllers)
    print
    print "*** Hosts addresses:"
    print
    for host in network.hosts:
        print host.name, host.IP()
    print

    print "Waiting for the controller to finish network setup..."
    countdown(3)
    print "PingAll to make sure everything's OK"
    network.pingAllFull()
    return network


def runExp():
    code = call(expanduser("~/scripts/run_senders.sh"))
    if code:
        print "Simulation ended with non zero returncode: " + str(code)


def cleanup(network):
    print "Killing ITGRecv(s)..."
    for host in network.hosts:
        host.cmd('kill %' + '/usr/sbin/sshd')
        host.cmd( 'pkill -15 ITGRecv.sh')
    print "Stopping the network..."
    network.stop()


if __name__ == '__main__':
    {2}
    {3}
    net = setupITG(setupNetwork(controller_ip))
    runExp()
    cleanup(net)
'''


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",required=True, help="The input file")
    parser.add_argument("-o", "--output", default="", help="The output file")
    parser.add_argument("-b", "--bandwidth", default="10", help="Bandwidth")
    parser.add_argument("--switch-bandwidth", default="100", help="Switch Bandwidth")
    parser.add_argument("-c", "--controller-ip", required=True, help="The Controller's IP address")
    parser.add_argument("-d", "--debug", action="store_true", help="Set mininet verbosity to high (debug level)")

    args = parser.parse_args()

    if args.output == "":
        args.output = args.input + '-generated-Mininet-Topo.py'
    return args


def get_graph_sets_from_xml(input_file, ns = "{http://graphml.graphdrawing.org/xmlns}"):
    # READ FILE AND DO ALL THE ACTUAL PARSING IN THE NEXT PARTS
    xml_tree = ElementTree.parse(input_file)
    # GET ALL ELEMENTS THAT ARE PARENTS OF ELEMENTS NEEDED LATER ON
    root_element = xml_tree.getroot()
    graph_element = root_element.find(ns + 'graph')
    # GET ALL ELEMENT SETS NEEDED LATER ON
    index_values_set = root_element.findall(ns + 'key')
    node_set = graph_element.findall(ns + 'node')
    edge_set = graph_element.findall(ns + 'edge')
    return edge_set, node_set, index_values_set

def remove_bad_chars(text):
    chars = "\ `*_{}[]()>#+-.,!$?'"
    for c in chars:
        if c in text:
            text = text.replace(c, "")
    return text


def get_dicts_from_node_set(node_set, index_values_set, ns = "{http://graphml.graphdrawing.org/xmlns}"):
    # SET SOME VARIABLES TO SAVE FOUND DATA FIRST
    # memorize the values' ids to search for in current topology
    node_label_name_in_graphml = ''
    node_latitude_name_in_graphml = ''
    node_longitude_name_in_graphml = ''
    # for saving the current values
    node_name_value = ''
    node_longitude_value = ''
    node_latitude_value = ''
    # id:value dictionaries
    id_node_name_dict = {}  # to hold all 'id: node_name_value' pairs
    id_longitude_dict = {}  # to hold all 'id: node_longitude_value' pairs
    id_latitude_dict = {}  # to hold all 'id: node_latitude_value' pairs
    # FIND OUT WHAT KEYS ARE TO BE USED, SINCE THIS DIFFERS IN DIFFERENT GRAPHML TOPOLOGIES
    for i in index_values_set:
        if i.attrib['attr.name'] == 'label' and i.attrib['for'] == 'node':
            node_label_name_in_graphml = i.attrib['id']
        if i.attrib['attr.name'] == 'Longitude':
            node_longitude_name_in_graphml = i.attrib['id']
        if i.attrib['attr.name'] == 'Latitude':
            node_latitude_name_in_graphml = i.attrib['id']

    # NOW PARSE ELEMENT SETS TO GET THE DATA FOR THE TOPO
    # GET NODE_NAME DATA
    # GET LONGITUDE DATK
    # GET LATITUDE DATA
    for n in node_set:

        node_index_value = n.attrib['id']

        # get all data elements residing under all node elements
        data_set = n.findall(ns + 'data')

        # finally get all needed values
        for d in data_set:

            # node name
            if d.attrib['key'] == node_label_name_in_graphml:
                # TODO: check this
                # strip all whitespace from names so they can be used as id's
                node_name_value = remove_bad_chars(d.text)
            # longitude data
            if d.attrib['key'] == node_longitude_name_in_graphml:
                node_longitude_value = d.text
            # latitude data
            if d.attrib['key'] == node_latitude_name_in_graphml:
                node_latitude_value = d.text

            # save id:data couple
            id_node_name_dict[node_index_value] = node_name_value
            id_longitude_dict[node_index_value] = node_longitude_value
            id_latitude_dict[node_index_value] = node_latitude_value
    return id_node_name_dict, id_longitude_dict, id_latitude_dict


def int2dpid(dpid):
    try:
        dpid = hex(dpid)[2:]
        dpid = '0' * ( 16 - len( dpid ) ) + dpid
        return dpid
    except IndexError:
        raise Exception('Unable to derive default datapath ID - '
                        'please either specify a dpid or use a '
                        'canonical switch name such as s23.' )


def add_switches_with_linked_host(id_node_name_dict):
    output = ''
    for i in range(0, len(id_node_name_dict)):
        id = str(i)
        name = id_node_name_dict[id]
        short_name = name[0:4]
        # create switch
        output += "        %s = self.addSwitch( '%s' , dpid='%s')\n"%(name,short_name,int2dpid(i))
        # create corresponding host
        output += "        %s_host = self.addHost( '%s-HST' )\n"%(name,short_name)
        # link each switch and its host...
        output += "        self.addLink(%s, %s_host)\n"%(name,name)
    return output


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
    return (distance * 1000) / (197000)


def add_switch_links(edge_set, id_node_name_dict, id_longitude_dict, id_latitude_dict, bandwidth):
    switch_links = ""
    for e in edge_set:

        # GET IDS FOR EASIER HANDLING
        src_id = e.attrib['source']
        dst_id = e.attrib['target']

        latency = calculate_latency(id_latitude_dict[src_id],
                                    id_latitude_dict[dst_id],
                                    id_longitude_dict[src_id],
                                    id_longitude_dict[dst_id])

        # ... and link all corresponding switches with each other
        name_src = id_node_name_dict[src_id]
        name_dst = id_node_name_dict[dst_id]
        switch_links += "        self.addLink(%s, %s, bw=%s, delay='%dms')\n"%(name_src,name_dst,bandwidth,latency)
    return switch_links


if __name__ == '__main__':
    args = parse_arguments()

    if args.debug:
        logging_output = "setLogLevel('debug')"
    else:
        logging_output = "setLogLevel('info')"

    edge_set, node_set, index_values_set = get_graph_sets_from_xml(args.input)

    id_node_name_dict, id_longitude_dict, id_latitude_dict = get_dicts_from_node_set(node_set, index_values_set)

    add_switches_with_linked_host_output = add_switches_with_linked_host(id_node_name_dict)

    add_switch_links_output = add_switch_links(edge_set, id_node_name_dict, id_longitude_dict, id_latitude_dict, args.switch_bandwidth)

    controller_ip_output = "controller_ip = '%s'"%args.controller_ip

    with open(args.output, 'w') as f:
        f.write(output_code.format(add_switches_with_linked_host_output,
                                   add_switch_links_output,
                                   logging_output,
                                   controller_ip_output))
    # give the output executable permissions
    st = os.stat(args.output)
    os.chmod(args.output, st.st_mode | 0111)

    print "Topology generation SUCCESSFUL!"
