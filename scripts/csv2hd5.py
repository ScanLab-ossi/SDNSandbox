#!/usr/bin/python

# GraphML-Topo-to-CSV
# This file parses Network Topologies in GraphML format from the Internet Topology Zoo.
# A CSV file describing the Topology will be created as Output.
#
#################################################################################
import argparse
from datetime import datetime
import logging

import pandas as pd

DATA_KEY = 'ifInOctets'

IF_INDEX_KEY = 'ifIndex'

UNIX_SECONDS_UTC_KEY = 'unixSecondsUTC'

requiredKeysSet = set([DATA_KEY, IF_INDEX_KEY, UNIX_SECONDS_UTC_KEY])


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--sflow-csv", required=True,
                        help="The input file - an sFlow CSV file")
    parser.add_argument("-l", "--links-csv", required=True,
                        help="CSV file describing the links in the topology")
    parser.add_argument("-i", "--intfs-list", required=True,
                        help="Input file listing the interfaces during the experiment")
    parser.add_argument("-t", "--titles", default="csv_titles",
                        help="The input file titles")
    parser.add_argument("-n", "--normalize-by", default="1000000", type=float,
                        help="The factor to normalize the input by")
    parser.add_argument("-o", "--output", default="",
                        help="The output file - an HD5 file representing [time,node]=speed")
    parser.add_argument("-k", "--hdf-key", default="sFlow_samples",
                        help="Identifier for the group in the HDF5 store.")
    parser.add_argument("-d", "--debug", action='store_true',
                        help="Set to add debug level log")
    args = parser.parse_args()
    if args.output == "":
        args.output = args.sflow_csv + '.hd5'
    return args


def get_samples_df(sflow_samples_csv, normalization_factor):
    samples = pd.read_csv(sflow_samples_csv, header=None, names=titles)
    df = pd.DataFrame()
    last = {}
    first_sampling_cycle = True
    prev_timestamp = None
    new_sampling_cycle = False
    sampling = {}
    for _, row in samples.iterrows():
        logging.debug("row=%s", row)
        timestamp = datetime.fromtimestamp(row[UNIX_SECONDS_UTC_KEY])
        if prev_timestamp is None:
            prev_timestamp = timestamp
        if not prev_timestamp == timestamp:
            first_sampling_cycle = False
            new_sampling_cycle = True
            prev_timestamp = timestamp
        else:
            new_sampling_cycle = False
        if_index = row[IF_INDEX_KEY]
        data = row[DATA_KEY] / normalization_factor
        if not first_sampling_cycle:
            logging.debug("first_sampling_cycle=%s, timestamp=%s, if_index=%s, data=%s, last[if_index]=%s",
                          first_sampling_cycle, timestamp, if_index, data, last[if_index])
            # if new cycle & the sampling cycle wasn't empty
            if new_sampling_cycle and sampling:
                df[timestamp] = pd.Series(sampling)
                sampling.clear()
            sampling[if_index] = data - last[if_index]
        last[if_index] = data
    return df


def get_irrelevant_switch_num_set(intfs_list_filename, switch_names_set):
    irrelevant_switch_num_set = set()
    with open(intfs_list_filename) as intfs_list:
        for row in intfs_list:
            if_num, if_name = row.split(': ')
            if_parts = if_name.split('@')
            if len(if_parts) == 2:
                if not {name.split('-')[0] for name in if_parts}.issubset(switch_names_set):
                    irrelevant_switch_num_set.add(int(if_num))
            else:
                irrelevant_switch_num_set.add(int(if_num))
    return irrelevant_switch_num_set


if __name__ == '__main__':
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    with open(args.titles) as f:
        titles = f.readline().split(',')

    if not requiredKeysSet.issubset(titles):
        logging.critical("One of required column titles [{0}] missing from input titles [{1}]",
                         requiredKeysSet, titles)
        exit(-1)

    df = get_samples_df(args.sflow_csv, args.normalize_by)

    links_df = pd.read_csv(args.links_csv, dtype={'From': 'str', 'To': 'str'})
    switch_names_set = set([link[0] for link in links_df.values] + [link[1] for link in links_df.values])

    irrelevant_switch_num_set = get_irrelevant_switch_num_set(args.intfs_list, switch_names_set)

    switch_drop_list = list(filter(lambda k: k in irrelevant_switch_num_set, df.T.keys()))

    df = df.drop(labels=switch_drop_list)

    df.T.to_hdf(args.output, key=args.hdf_key, mode='w')

    logging.info("sFlow CSV to HDF5 SUCCESSFUL!")
