#!/usr/bin/python

# plot_hd5
# This script will plot an HD5 file.
#
#################################################################################
import argparse
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from os.path import join as pj
from os.path import dirname
from os import mkdir


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sflow-hd5", required=True,
                        help="The input file - an sFlow HD5 file")
    parser.add_argument("-k", "--hdf-key", default="sFlow_samples",
                        help="Identifier for the group in the HDF5 store.")
    parser.add_argument("-o", "--output-base-path", default="plots",
                        help="Base path to output plots to - defaults to <HD5_path>/plots/.")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="Set to add debug level log")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    logging.info("Reading HD5 file " + args.sflow_hd5)
    df = pd.read_hdf(args.sflow_hd5, key=args.hdf_key)
    logging.info("Found " + str(len(df.keys())) + " keys in the file")
    logging.info("The following keys were found: " + str(df.keys()))
    plots_dir = pj(dirname(args.sflow_hd5), args.output_base_path)
    logging.info("Creating directory " + plots_dir + " for plots")
    mkdir(plots_dir)
    for i in df.keys():
        logging.info("Plotting samples for port " + str(i))
        df[i].plot()
        plt.xlabel('Time')
        plt.ylabel('MB/s')
        plt.tight_layout()
        filename = pj(plots_dir, "link_load_" + str(i) + ".png")
        logging.info("Saving plot to " + filename)
        plt.savefig(filename)
        plt.close()
