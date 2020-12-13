import logging
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.util import dumpNetConnections
from os.path import join as pj
from sdnsandbox.util import countdown


logger = logging.getLogger(__name__)


class Runner(object):
    def __init__(self, topology, controller, load_generator, monitor, output_dir, ping_all_full=False):
        self.net = Mininet(topo=topology, controller=lambda unneeded: controller, link=TCLink)
        self.load_generator = load_generator
        self.monitor = monitor
        self.output_dir = output_dir
        self.ping_all_full = ping_all_full

    def run(self):
        self.run_network()
        self.load_generator.start_receivers(self.net, self.output_dir)
        self.monitor.start_monitoring(self.output_dir)
        self.load_generator.run_senders(self.net, self.output_dir)

    def stop_and_save_monitoring_data(self):
        self.monitor.stop_monitoring_and_save()
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
