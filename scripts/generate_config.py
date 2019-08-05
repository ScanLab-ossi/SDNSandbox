#!/usr/bin/python
import argparse
import logging
import random
import os
from netaddr import iter_iprange, IPAddress

baseCommand = "timeout %s ITGSend"

graceSeconds = 3

# IPs
firstHost = "10.0.0.1"
lastHostTemplate = "10.0.0."


def return_imix_packet_options():
    # All values based roughly on http://www.caida.org/research/traffic-analysis/AIX/plen_hist/
    variant_packet_size_mean = 576
    variant_packet_size_std_dev = 190  # makes 3-sigma between 50-1400 packet sizes be 99,7%
    constant_packet_size = 1500

    constant_pps = 250

    randomly = random.randint(1, 100)
    # The split shown was ~30% 40B, ~55% normal around 576B, ~15% 1500B
    # Therefore the normally distributed portion is:
    # 100 - (100 * 15 / (15 + 55)) = 78
    if 1 <= randomly < 78:
        # Normal Distribution for packet sizes
        opts = " -n %s %s" % (variant_packet_size_mean, variant_packet_size_std_dev)
    else:
        # Constant packet size
        opts = " -c %s" % constant_packet_size

    # Maxes at 3Mbps for 1500B packets - assumes we are using a 10Mbps line to insert load
    opts += " -C %s" % constant_pps
    return opts


def create_command(base, destination, protocol, duration):
    cmd_base = base % int(duration / 1000 + graceSeconds)
    cmd_base += " -a %s" % destination
    cmd_base += " -T %s" % protocol
    cmd_base += " -t %s" % duration
    cmd_base += return_imix_packet_options()
    cmd_base += " -l /dev/null"
    cmd = """
if ! %s ; then
    echo ITGSend failed... Trying again in 3 secs!
    sleep 3
    if ! %s ; then
        echo ITGSend to %s failed, skipping this command!
    fi
fi""" % (cmd_base, cmd_base, destination)
    return cmd


def create_dynamic_load_commands(hosts, protocol, periods, period_length_milliseconds):
    commands = []
    for _ in range(periods):
        loaded_host = hosts[random.randrange(len(hosts))]
        cmd = create_command(baseCommand,
                             loaded_host,
                             protocol,
                             period_length_milliseconds)
        commands.append(cmd)
    return commands


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
    parser.add_argument("-p", "--periods", type=int, default=360,
                        help="The number of experiment periods in the configuration files")
    parser.add_argument("-l", "--period-length", type=int, default=100000,
                        help="The length of an experiment period in milliseconds")
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
        load_generating_commands = create_dynamic_load_commands(loaded_addresses,
                                                                args.protocol,
                                                                args.periods,
                                                                args.period_length)
        logging.debug(load_generating_commands)
        write_commands_to_file(load_generating_commands, args.config_dir + "/config-" + address)

    logging.info("Done generating host config files!")
