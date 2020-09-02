#!/usr/bin/python
import argparse
import logging
import os

# IPs
firstHost = "10.0.0.1"
hostTemplate = "10.0.0."


def create_command(params, host_id):
    multiflow_filename = "/tmp/ITGSend_multiflow_%s" % host_id

    ITGSend_cmd = get_ITGSend_cmd(multiflow_filename,
                                  params.period_length,
                                  params.grace_period,
                                  params.sleep_period)

    sed_cmds = get_sed_cmds(multiflow_filename, params, host_id)
    dests = "DESTS=(`seq 1 %d ; seq %d %d`)" %\
            (host_id - 1, host_id + 1, params.num_hosts)
    cp_cmd = "cp scripts/ITGSend_IMIX_multiflow_%s %s" %\
             (params.protocol, multiflow_filename)
    cmd = """
%s

for period in {1..%d}
do

echo "Preparing period #$period..."
%s
%s
echo "Running period #$period..."
%s

done""" % (dests, params.periods, cp_cmd, sed_cmds, ITGSend_cmd)
    return cmd


def get_ITGSend_cmd(multiflow_filename, duration_ms, grace_period, sleep_period):
    send_cmd = "timeout %d ITGSend %s -l /dev/null" %\
          (int(grace_period + duration_ms / 1000), multiflow_filename)
    cmd = "echo \"Using following multiflow commands:\"; cat %s\n" \
          "date; %s; STATUS=$?\n" \
          "if [ ! $STATUS ]; then \n" \
          "echo \"ITGSend failed with status code $STATUS ... Trying again in %d secs!\"\n"\
          "sleep %d \n" \
          "date; %s; STATUS=$?\n" \
          "[ ! $STATUS ] && echo \"ITGSend failed again (with status code $STATUS )\"\nfi" %\
          (multiflow_filename, send_cmd, sleep_period, sleep_period, send_cmd)
    return cmd


def get_sed_cmds(filename, params, host_id):
    # remove explanatory comments from file (ITGSend can't handle them)
    sed_cmds = "sed -i /^\#/d %s \n" % filename

    sed_cmds += "sed -i s/destination/%s${DESTS[$(( ($period+%d) %% %d ))]}/g %s \n" %\
                (hostTemplate, host_id, params.num_hosts - 1, filename)

    sed_cmds += "sed -i s/duration/%d/g %s \n" % (params.period_length, filename)

    # 2pi is the regulat wavelength of sine, so we divide it by the required wavelength
    awk_2pi = "2*atan2(0,-1)"
    pps_wavelength = awk_2pi + "/" + str(params.pps_wavelength)

    sed_cmds += "PPS=`awk \"BEGIN{print %d+int(%d*sin($period*%s))}\"` \n" %\
                (params.pps_base_level, params.pps_amplitude, pps_wavelength)
    # The IMIX split shown was ~30% 40B, ~55% normal around 576B, ~15% 1500B
    # The 190 standard deviation makes 3-sigma between 50-1400 packet sizes be 99,7%
    # All values based roughly on http://www.caida.org/research/traffic-analysis/AIX/plen_hist/
    if params.protocol == 'TCP':
        # Therefore to get a similar distribution with TCP (which has builtin 40B ACKs):
        # Normal distribution with [100 - (100 * 15 / (15 + 55))] = 78%
        sed_cmds += "sed -i s/pps_normal/`awk \"BEGIN{print int(0.78 * $PPS)}\"`/g %s \n" %\
                    filename
        # Constant packet size - high - 22%
        sed_cmds += "sed -i s/pps_high/`awk \"BEGIN{print int(0.22 * $PPS)}\"`/g %s \n" %\
                    filename
    elif params.protocol == 'UDP':
        # Therefore to get a similar distribution with UDP:
        # Constant packet size - low 30%
        sed_cmds += "sed -i s/pps_low/`awk \"BEGIN{print int(0.3 * $PPS)}\"`/g %s \n" %\
                    filename
        # Normal Distribution for packet sizes - 55%
        # The 190 standard deviation makes 3-sigma between 50-1400 packet sizes be 99,7%
        sed_cmds += "sed -i s/pps_normal/`awk \"BEGIN{print int(0.55 * $PPS)}\"`/g %s \n" %\
                    filename
        # Constant packet size - high - 15%
        sed_cmds += "sed -i s/pps_high/`awk \"BEGIN{print int(0.15 * $PPS)}\"`/g %s \n" %\
                    filename
    return sed_cmds


def write_script_to_file(commands, filename):
    logging.info("Writing to %s", filename)
    with open(filename, "w") as f:
        f.write("#!/bin/bash"+os.linesep)
        f.write(commands+os.linesep)
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
    logging.info("Got valid args:")
    for arg, value in sorted(vars(args).items()):
        logging.info("Argument %s: %r", arg, value)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--config-dir", required=True,
                        help="The configuration file directory (where the config files will be written to)")
    parser.add_argument("--protocol", default="UDP", choices=['UDP', 'TCP'],
                        help="The transmission protocol to be used")
    parser.add_argument("-n", "--num-hosts", type=int, required=True,
                        help="The number of hosts to generate configuration files for")
    parser.add_argument("-p", "--periods", type=int, default=360,
                        help="The number of experiment periods in the configuration files")
    parser.add_argument("-l", "--period-length", type=int, default=30000,
                        help="The length of an experiment period in milliseconds")
    parser.add_argument("-g", "--grace-period", type=int, default=6,
                        help="The length of a grace period (in seconds) "
                             "before calling a timeout on the period's sender")
    parser.add_argument("-s", "--sleep-period", type=int, default=3,
                        help="The length of a sleep period (in seconds) after failure"
                             "in order to allow the sender/receiver to stabilize between runs")
    parser.add_argument("--pps-base-level", type=int, default=150,
                        help="The base level of the pps sine load curve")
    parser.add_argument("--pps-amplitude", type=int, default=100,
                        help="The amplitude of the pps sine load curve")
    parser.add_argument("--pps-wavelength", type=int, default=60,
                        help="The wavelength of the pps sine load curve - in periods")
    parser.add_argument("--debug", action="store_true", help="Set verbosity to high (debug level)")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    validate_args(args)

    logging.info("Generating load generation scripts...")

    for host in range(1, args.num_hosts+1):
        address = hostTemplate + str(host)
        logging.info("Creating script for " + address)
        write_script_to_file(create_command(args, host), args.config_dir + "/config-" + address + ".sh")

    logging.info("Done generating host config files!")
