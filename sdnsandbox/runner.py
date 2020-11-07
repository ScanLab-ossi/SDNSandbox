import logging
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNetConnections
from os.path import join as pj
from sdnsandbox.util import countdown
from ifaddr import get_adapters


class Runner(object):
    def __init__(self, topology, controller, load_generator, monitor, output_dir):
        self.net = self.setup_network(topology, controller)
        self.load_generator = load_generator
        self.monitor = monitor
        self.output_dir = output_dir

    def run(self):
        self.load_generator.start_receivers(self.net, self.output_dir)
        self.monitor.start_monitoring()
        self.load_generator.run_senders(self.net, self.output_dir)

    def save_monitoring_data_and_stop(self,
                                      interfaces_filename="interfaces",
                                      monitoring_data_filename="monitoring_data"):
        self.save_interfaces_list(pj(self.output_dir, interfaces_filename))
        self.monitor.save_monitoring_data_and_stop(pj(self.output_dir, monitoring_data_filename))
        self.load_generator.stop_receivers(self.net)
        logging.info("Stopping the network...")
        self.net.stop()

    @staticmethod
    def setup_network(topology, controller):
        """Create network and start it"""
        network = Mininet(topo=topology, controller=controller, link=TCLink)

        logging.info("Waiting for the controller to finish network setup...")
        countdown(3)

        dumpNetConnections(network)
        logging.info("PingAll to make sure everything's OK")
        network.pingAllFull()
        return network

    @staticmethod
    def save_interfaces_list(interfaces_filename):
        with open(interfaces_filename, 'w') as f:
            f.write(get_adapters())
