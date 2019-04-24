#!/usr/bin/python
import argparse
import logging
import random
import os
from netaddr import iter_iprange, IPAddress

baseCommand = "sleep %d ; ITGSend"

# IPs
firstHost = "10.0.0.1"
lastHostTemplate = "10.0.0."

# Packets per Second range for Poisson distribution of inter-departure time
dynamicPPS = {
    "min": 330,  # ~20% of 10 Mbit for 600 byte mean
    "max": 1000  # ~60% of 10Mbit for 600 byte mean
}
# Based roughly on http://www.caida.org/research/traffic-analysis/AIX/plen_hist/
packetSizeMean = 600
packetSizeStdDev = 100


def create_command(base, dest, protocol, duration, delay_secs, pps, packet_size_mean, packet_size_std_dev):
    cmd = base % delay_secs
    cmd += " -a %s" % dest
    cmd += " -T %s" % protocol
    cmd += " -t %s" % duration
    cmd += " -O %s" % pps
    cmd += " -n %s %s" % (packet_size_mean, packet_size_std_dev)
    cmd += " < /dev/null &"
    return cmd


def create_dynamic_loader_commands(hosts, protocol, periods, period_length_milliseconds, diff_abs):
    commands = []
    pps = random.randrange(dynamicPPS["min"], dynamicPPS["max"])
    diff = set_diff(pps, diff_abs)
    for i in range(periods):
        delay_secs = period_length_milliseconds / 1000
        loaded_host = hosts[i % len(hosts)]
        cmd = create_command(baseCommand,
                             loaded_host,
                             protocol,
                             period_length_milliseconds,
                             delay_secs,
                             pps,
                             packetSizeMean, packetSizeStdDev)
        commands.append(cmd)
        pps += diff
        if pps < dynamicPPS["min"] or pps > dynamicPPS["max"]:
            diff = -diff
            pps += 2*diff
    return commands


def set_diff(pps, diff_abs):
    if (pps - dynamicPPS["min"]) / (dynamicPPS["max"] - dynamicPPS["min"]) > 0.5:
        return diff_abs
    else:
        return -diff_abs


def write_commands_to_file(commands, filename):
    logging.info("Writing to %s", filename)
    with open(filename, "w") as f:
        f.write("#!/bin/bash"+os.linesep)
        for c in commands:
            f.write(c + os.linesep)
        f.write("wait"+os.linesep)
    # give it executable permissions
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | 0o0111)


def validate_args(args):
    if os.path.isdir(args.config_dir):
        logging.info("Creating config files in dir: %s", args.config_dir)
    else:
        logging.fatal("Argument specified \"%s\" is not a directory!", args.config_dir)
        exit(1)
    if not 1 <= args.num_hosts <= 253:
        logging.fatal(
            """The number of hosts specified \"%d\" cannot be within one subnet!
Should be {1..253}!""",
            args.num_hosts)
        exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--config-dir", required=True,
                        help="The configuration file directory (where the config files will be written to)")
    parser.add_argument("--protocol", default="TCP",
                        help="The transmission protocol to be used")
    parser.add_argument("-n", "--num-hosts", type=int, required=True,
                        help="The number of hosts to generate configuration files for")
    parser.add_argument("-p", "--periods", type=int, default=3600,
                        help="The number of experiment periods in the configuration files")
    parser.add_argument("-l", "--period-length", type=int, default=10000,
                        help="The length of an experiment period in milliseconds")
    parser.add_argument("-a", "--absolute-pps-difference", type=int, default=10,
                        help="The amount to increase/decrease the pps by per period")
    parser.add_argument("--debug", action="store_true", help="Set verbosity to high (debug level)")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    validate_args(args)

    logging.info("Generating with %d periods", args.periods)

    last_host = lastHostTemplate + str(args.num_hosts)
    ip_addresses = list(iter_iprange(firstHost, last_host, step=1))

    logging.info("Creating configuration for IPs:")
    logging.info(ip_addresses)

    for address in ip_addresses:
        address = str(address)
        logging.info("Creating commands for " + address)
        loaded_addresses = list(ip_addresses)
        # Remove localhost address
        loaded_addresses.remove(IPAddress(address))
        commands = create_dynamic_loader_commands(loaded_addresses,
                                                  args.protocol,
                                                  args.periods,
                                                  args.period_length,
                                                  args.absolute_pps_difference)
        logging.debug(commands)
        write_commands_to_file(commands, args.config_dir + "/config-" + address)

    logging.info("Done generating host config files!")
