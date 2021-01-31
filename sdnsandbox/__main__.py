import sys
from os import makedirs
from mininet.log import setLogLevel
import logging
import argparse
from os.path import join as pj

from sdnsandbox.runner import RunnerFactory


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
    parser.add_argument("-d", "--debug", action="store_true", help="Set SDNSandbox verbosity to debug level")
    parser.add_argument("--mininet-debug", action="store_true", help="Set mininet verbosity to debug level")
    return parser.parse_args()


args = parse_arguments()
logs_path = pj(args.output_dir, "logs")
makedirs(logs_path)
setup_logging(args.debug, args.mininet_debug, logs_path)
runner = RunnerFactory.create(args.config, args.output_dir, logs_path)
try:
    runner.run()
except KeyboardInterrupt:
    logging.fatal("Interrupted during experiment... Attempting to clean up and exiting...")
finally:
    runner.stop_and_save()
    logging.info('The experiment files can be found @ %s', args.output_dir)
    logging.info('NOTE: If the experiment was run inside a Docker container,'
                 ' the actual location depends on the volume mount')
