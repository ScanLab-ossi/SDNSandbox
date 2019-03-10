#!/usr/bin/python

# GraphML-Topo-to-CSV
# This file parses Network Topologies in GraphML format from the Internet Topology Zoo.
# A CSV file describing the Topology will be created as Output.
#
#################################################################################
import argparse
from datetime import datetime

import pandas as pd

DATA_KEY = 'ifInOctets'

IF_INDEX_KEY = 'ifIndex'

UNIX_SECONDS_UTC_KEY = 'unixSecondsUTC'

requiredKeysSet = set([DATA_KEY, IF_INDEX_KEY, UNIX_SECONDS_UTC_KEY])


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="The input file - an sFlow CSV file")
    parser.add_argument("-t", "--titles", default="csv_titles", help="The input file titles")
    parser.add_argument("-o", "--output", default="",
                        help="The output file - an HD5 file representing [time,node]=speed")
    parser.add_argument("-k", "--hdf-key", default="sFlow_samples", help="Identifier for the group in the HDF5 store.")
    args = parser.parse_args()
    if args.output == "":
        args.output = args.input + '.hd5'
    return args


if __name__ == '__main__':
    args = parse_arguments()

    with open(args.titles) as f:
        titles = f.readline().split(',')

    if not requiredKeysSet.issubset(titles):
        print("One of required column titles [{0}] missing from input titles [{1}]"
              .format(requiredKeysSet, titles))
    samples = pd.read_csv(args.input, header=None, names=titles)

    df = pd.DataFrame()
    last = {}
    firstSamplingCycle = True
    prevTimestamp = None
    newSamplingCycle = False
    sampling = {}
    for _, row in samples.iterrows():
        # print(row)
        timestamp = datetime.fromtimestamp(row[UNIX_SECONDS_UTC_KEY])
        if prevTimestamp is None:
            prevTimestamp = timestamp
        if not prevTimestamp == timestamp:
            firstSamplingCycle = False
            newSamplingCycle = True
            prevTimestamp = timestamp
        else:
            newSamplingCycle = False
        ifIndex = row[IF_INDEX_KEY]
        data = row[DATA_KEY]
        if not firstSamplingCycle:
            # print(firstTimestamp, firstSamplingCycle, timestamp, ifIndex, data, last[ifIndex])
            if newSamplingCycle:
                print(sampling)
                df[timestamp] = pd.Series(sampling)
            sampling[ifIndex] = data - last[ifIndex]
        last[ifIndex] = data

    df.T.to_hdf(args.output, key=args.hdf_key, mode='w')

    print("sFlow CSV to HDF5 SUCCESSFUL!")
