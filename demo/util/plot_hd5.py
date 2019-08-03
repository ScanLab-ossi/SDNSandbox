#!/usr/bin/python

# plot_hd5
# This script will plot an HD5 file.
#
#################################################################################
import argparse
import logging
import matplotlib.pyplot as plt
import pandas as pd


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sflow-hdf", required=True,
                        help="The input file - an sFlow CSV file")
    parser.add_argument("-k", "--hdf-key", default="sFlow_samples",
                        help="Identifier for the group in the HDF5 store.")
    parser.add_argument("-o", "--output-base-path", default="sFlow_samples",
                        help="Base path to output plots to.")
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

    logging.info("Reading HD5 file " + args.sflow_hdf)
    df = pd.read_hdf(args.sflow_hdf, key=args.hdf_key)
    logging.info("Found " + str(len(df.keys())) + " keys in the file")
    logging.info("The following keys were found: " + str(df.keys()))
    for i in df.keys():
        logging.info("Plotting samples for port " + str(i))
        df[i].plot()
        plt.xlabel('Time')
        plt.ylabel('MB/s')
        plt.tight_layout()
        filename = args.output_base_path + "_port_" + str(i) + ".png"
        logging.info("Saving plot to " + filename)
        plt.savefig(filename)
        plt.close()
