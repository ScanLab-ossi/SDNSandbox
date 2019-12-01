#!/usr/bin/env python

# calc_hd5_iqr.py
# This script will calculate an HD5 file's IQR (interquartile range).
#
#################################################################################
import argparse
import logging
import pandas as pd
from scipy.stats import iqr
import json


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sflow-hdf", required=True,
                        help="The input file - an sFlow CSV file")
    parser.add_argument("-k", "--hdf-key", default="sFlow_samples",
                        help="Identifier for the group in the HDF5 store.")
    parser.add_argument("-o", "--output-path", default="",
                        help="Path to output IQR results to, defaults to '<input-file>-iqr.json'.")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="Set to add debug level log")
    args = parser.parse_args()
    if args.output_path == "":
        args.output_path = args.sflow_hdf + '-iqr.json'
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

    results = {}

    total_values = df.values
    total_iqr = iqr(total_values)
    results['total_iqr'] = {'result': total_iqr,
                            'instances_for_calc': total_values.size,
                            'description': 'IQR for all readings'}
    logging.info(results['total_iqr']['description'] + " is " + str(results['total_iqr']['result']))

    total_iqr_nan_omitted = iqr(total_values, nan_policy='omit')
    results['total_iqr_nan_omitted'] = {'result': total_iqr,
                                        'instances_for_calc': total_values.size - sum(df.isnull().sum()),
                                        'description': 'IQR for all readings except NaN'}
    logging.info(results['total_iqr_nan_omitted']['description'] + " is " +
                 str(results['total_iqr_nan_omitted']['result']))

    df_t_mean = df.T.mean()
    df_t_iqr = iqr(df_t_mean)
    results['second_means_iqr'] = {'result': df_t_iqr,
                                   'instances_for_calc': len(df_t_mean),
                                   'description': 'IQR for means of all seconds (mean of all readings per second)'}
    logging.info(results['second_means_iqr']['description'] + " is " + str(results['second_means_iqr']['result']))

    df_mean = df.mean()
    df_iqr = iqr(df_mean)
    results['port_means_iqr'] = {'result': df_iqr,
                                 'instances_for_calc': len(df_mean),
                                 'description': 'IQR for port means (mean of all the readings a port had)'}
    logging.info(results['port_means_iqr']['description'] + " is " + str(results['port_means_iqr']['result']))

    logging.info("Dumping results to " + args.output_path)
    logging.debug("JSON will be created from: %s", str(results))
    with open(args.output_path, 'w') as f:
        json.dump(results, f, indent=4, separators=(',', ': '))
