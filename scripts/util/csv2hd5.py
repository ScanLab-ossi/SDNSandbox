#!/usr/bin/python

# csv2hd5
# This script will transform the CSV sFlow output to
# a more dense and self describing HD5 file format.
#
#################################################################################
import argparse
from collections import namedtuple
from datetime import datetime
import logging

import pandas as pd
import numpy as np
import traceback

Link = namedtuple('Link', 'From_ID, From_Name, To_ID, To_Name, Latency_in_ms')

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
    parser.add_argument("-n", "--normalize-by", default=2**20, type=float,
                        help="The factor to normalize the input by - defaults to Mega(2^20)")
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
    samples = pd.read_csv(sflow_samples_csv, dtype=np.uint64, header=None, names=titles)
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
        if not first_sampling_cycle and if_index in last:
            logging.debug("first_sampling_cycle=%s, timestamp=%s, if_index=%s, data=%s, last[if_index]=%s",
                          first_sampling_cycle, timestamp, if_index, data, last[if_index])
            # if new cycle & the sampling cycle wasn't empty
            if new_sampling_cycle and sampling:
                df[timestamp] = pd.Series(sampling)
                sampling.clear()
            sampling[if_index] = data - last[if_index]
        last[if_index] = data
    return df


def get_relevant_interface_num_to_name_map(intfs_list_filename, switch_ids_to_names):
    interface_num_to_name_map = {}
    with open(intfs_list_filename) as intfs_list:
        for row in intfs_list:
            if_num, if_name = row.split(': ')
            # make the num an int
            if_num = int(if_num)
            # remove excess whitespace
            if_name = if_name.strip()
            # interface names listed will be in format s<switch-id>-<port-in-switch> twice with @ as delimiter
            if_parts = if_name.split('@')
            logging.info("found interface: \n%s", if_parts)
            if len(if_parts) == 2:
                if_switch_ids = [name.split('-')[0][1:] for name in if_parts]
                logging.info("found if_switch_ids: \n%s", if_switch_ids)
                if set(if_switch_ids).issubset(switch_ids_to_names.keys()):
                    sw_id = if_switch_ids[0]
                    new_name = if_name.replace("s"+sw_id,switch_ids_to_names[sw_id])
                    sw_id = if_switch_ids[1]
                    new_name = new_name.replace("s"+sw_id,switch_ids_to_names[sw_id])
                    interface_num_to_name_map[if_num] = new_name
                else:
                    logging.info("interface ids aren't both in the experiment switch ids, irrelevant - dropped...")
            else:
                logging.info("interface doesn't have two parts, irrelevant - dropped...")
    return interface_num_to_name_map


if __name__ == '__main__':
    args = parse_arguments()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    try:
        with open(args.titles) as f:
            titles = f.readline().split(',')
    
        if not requiredKeysSet.issubset(titles):
            logging.critical("One of required column titles [{-1}] missing from input titles [{1}]",
                             requiredKeysSet, titles)
            exit(-2)
    
        links_df = pd.read_csv(args.links_csv,
                               dtype={'From_ID': 'str',
                                      'From_Name': 'str',
                                      'To_ID': 'str',
                                      'To_Name': 'str',
                                      'Latency_in_ms': 'float'})
        logging.info("Links found: \n%s", links_df)

        switch_ids_to_names = {}
        for link in links_df.values:
            link_tuple = Link(*link)
            switch_ids_to_names[link_tuple.From_ID] = link_tuple.From_Name
            switch_ids_to_names[link_tuple.To_ID] = link_tuple.To_Name
        logging.info("Switches found: \n%s", sorted(switch_ids_to_names))

        relevant_interface_num_to_name_map = get_relevant_interface_num_to_name_map(args.intfs_list, switch_ids_to_names)
        logging.info("Relevant ports found: \n%s", relevant_interface_num_to_name_map)

        df = get_samples_df(args.sflow_csv, args.normalize_by)
        logging.info('CSV dataframe:\n%s', df)

        port_drop_list = list(filter(lambda k: k not in relevant_interface_num_to_name_map.keys(), df.T.keys()))
        logging.info("dropping the following irrelevant ports from dataframe:\n%s", port_drop_list)
        df = df.drop(labels=port_drop_list)
        logging.debug('CSV dataframe after drop:\n%s', df)
    
        df.rename(relevant_interface_num_to_name_map, inplace=True)
        logging.debug('CSV dataframe after drop after rename:\n%s', df)

        logging.info('CSV dataframe will now be written to: %s', args.output)
        df.T.to_hdf(args.output, key=args.hdf_key, mode='w')
    except Exception as e:
        logging.info("Failure converting CSV " + args.sflow_csv + " to HDF5: " + traceback.format_exc())
        exit(-1)
    else:
        logging.info("sFlow CSV " + args.sflow_csv + " to HDF5 SUCCESSFUL!")
