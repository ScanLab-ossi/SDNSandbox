#!/usr/bin/python
import argparse
import logging
import os


def create_script_contents(template, params, host_id):
    multiflow_filename = os.path.join(params.tmp_multiflow_path, "ITGSend_multiflow_" + str(host_id))

    replacements = {
        "__tmp_file__": multiflow_filename,
        "__timeout_secs__": int(params.grace_period + params.period_duration / 1000),
        "__protocol__": params.protocol,
        "__periods__": params.periods,
        "__multiflow_path__": params.multiflow_path,
        "__hosts_template__": params.hosts_template,
        "__host_id__": host_id,
        "__num_hosts__": params.num_hosts,
        "__period_duration__": params.period_duration,
        "__pps_base_level__": params.pps_base_level,
        "__pps_amplitude__": params.pps_amplitude,
        "__pps_wavelength__": params.pps_wavelength,
        "__sleep_secs__": params.sleep_period
    }
    contents = template
    for old, new in replacements.items():
        contents = contents.replace(old, str(new))
    return contents


def write_script_to_file(commands, filename):
    logging.info("Writing to %s", filename)
    with open(filename, "w") as f:
        f.write(commands)
    # give it executable permissions
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | 0o0111)


def validate_args(args):
    for arg in [args.sender_dir, args.multiflow_path, args.tmp_multiflow_path]:
        if not os.path.isdir(arg):
            logging.fatal("Argument specified \"%s\" is not a directory!", arg)
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
    parser.add_argument("-d", "--sender-dir", required=True,
                        help="The sender script directory (where the scripts will be written to)")
    parser.add_argument("--protocol", default="UDP", choices=['UDP', 'TCP'],
                        help="The transmission protocol to be used")
    parser.add_argument("--hosts-template", default="10.0.0.",
                        help="The IP address template to be used, of form 'x.y.z.'")
    parser.add_argument("-m", "--multiflow-path", default="scripts",
                        help="The ITGSend multiflow template files location path")
    parser.add_argument("--tmp-multiflow-path", default="/tmp",
                        help="The temporary ITGSend multiflow files base path")
    parser.add_argument("-t", "--template-path", default="ITGSend_template",
                        help="The ITGSend sender script template file location path")
    parser.add_argument("-n", "--num-hosts", type=int, required=True,
                        help="The number of hosts to generate configuration files for")
    parser.add_argument("-p", "--periods", type=int, default=360,
                        help="The number of experiment periods in the configuration files")
    parser.add_argument("-l", "--period-duration", type=int, default=30000,
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

    logging.info("Creating sender scripts in dir: %s", args.sender_dir)
    logging.info("Generating load generation scripts...")

    logging.info("Using template from %s", args.template_path)
    template = None
    with open(args.template_path) as template_file:
        template = template_file.read()

    for host in range(1, args.num_hosts+1):
        address = args.hosts_template + str(host)
        logging.info("Creating script for " + address)
        script_contents = create_script_contents(template, args, host)
        write_script_to_file(script_contents, args.sender_dir + "/sender-" + address + ".sh")

    logging.info("Done generating host config files!")
