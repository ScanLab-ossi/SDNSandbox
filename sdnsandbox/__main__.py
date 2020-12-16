import sys
from socket import gethostbyname_ex
from sdnsandbox.runner import Runner
from sdnsandbox.topology import TopologyCreatorFactory
from sdnsandbox.load_generator import LoadGeneratorFactory
from sdnsandbox.monitor import MonitorFactory
from mininet.node import RemoteController
from mininet.log import setLogLevel
import logging
import argparse
from json import load
from os.path import join as pj


def setup_logging(sdnsandbox_debug, mininet_debug, output_dir):
    root_logger = logging.getLogger()
    if sdnsandbox_debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
    if mininet_debug:
        setLogLevel('debug')
    else:
        setLogLevel('info')
    fh = logging.FileHandler(pj(output_dir, 'sdnsandbox.log'))
    sh = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s->%(name)s-%(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    root_logger.addHandler(fh)
    root_logger.addHandler(sh)


def parse_arguments():
    parser = argparse.ArgumentParser(prog="sdnsandbox")
    parser.add_argument("-c", "--config", required=True, help="JSON configuration file")
    parser.add_argument("-o", "--output-dir", required=True, help="The experiment output directory")
    parser.add_argument("-d", "--debug", action="store_true", help="Set mininet verbosity to high (debug level)")
    parser.add_argument("--mininet-debug", action="store_true", help="Set mininet verbosity to high (debug level)")
    return parser.parse_args()


args = parse_arguments()
setup_logging(args.debug, args.mininet_debug, args.output_dir)
with open(args.config) as conf_file:
    conf = load(conf_file)
    topology_conf = conf['topology']
    controller_conf = conf['controller']
    runner_conf = conf['runner']
    load_generator_conf = conf['load_generator']
    monitor_conf = conf['monitor']

# we assume the first ip is enough, this works for both an IP address and DNS name
controller_ip = gethostbyname_ex(controller_conf['ip'])[2][0]
controller = RemoteController('controller', ip=controller_ip, port=controller_conf["port"])
load_generator = LoadGeneratorFactory.create(load_generator_conf)
topology_creator = TopologyCreatorFactory.create(topology_conf)
monitor = MonitorFactory().create(monitor_conf, {sw.ID: sw.name for sw in topology_creator.switches.values()})
topology = topology_creator.create()
runner = Runner(topology, controller, load_generator, monitor, args.output_dir, ping_all_full=runner_conf['pingAllFull'])
try:
    runner.run()
    runner.stop_and_save_monitoring_data()
except KeyboardInterrupt:
    logging.fatal("Interrupted during experiment... Attempting to clean up and exiting...")
    runner.stop_and_save_monitoring_data()
finally:
    logging.info('The experiment files can be found in %s', args.output_dir)
    logging.info('NOTE: If the experiment was run inside a Docker container, the location depends on the volume mount')
