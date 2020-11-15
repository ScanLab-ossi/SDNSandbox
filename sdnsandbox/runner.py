import logging
from json import dump

from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNetConnections
from os.path import join as pj
from sdnsandbox.util import countdown, get_interfaces


logger = logging.getLogger(__name__)


class Runner(object):
    def __init__(self, topology, controller, load_generator, monitor, output_dir, ping_all_full=False):
        self.net = Mininet(topo=topology, controller=lambda unneeded: controller, link=TCLink)
        self.load_generator = load_generator
        self.monitor = monitor
        self.output_dir = output_dir
        self.ping_all_full = ping_all_full

    def run(self,
            interfaces_filename="interfaces"):
        self.run_network()
        self.save_interfaces(pj(self.output_dir, interfaces_filename))
        self.load_generator.start_receivers(self.net, self.output_dir)
        self.monitor.start_monitoring(self.output_dir)
        self.load_generator.run_senders(self.net, self.output_dir)

    def save_monitoring_data_and_stop(self):
        self.monitor.stop_monitoring()
        self.load_generator.stop_receivers()
        logger.info("Stopping the network...")
        self.net.stop()

    def run_network(self):
        """Create network and start it"""
        self.net.start()

        logger.info("Waiting for the controller to finish network setup...")
        countdown(logger.info, 3)

        dumpNetConnections(self.net)
        if self.ping_all_full:
            logger.info("PingAll to make sure everything's OK")
            self.net.pingAllFull()
        return self.net

    @staticmethod
    def save_interfaces(interfaces_filename):
        interfaces = get_interfaces()
        with open(interfaces_filename, 'w') as f:
            dump(interfaces, f, sort_keys=True, indent=4)
