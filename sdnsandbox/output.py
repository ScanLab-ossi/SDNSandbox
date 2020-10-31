from datetime import datetime
import logging
import pandas as pd
import numpy as np

DATA_KEY = 'ifInOctets'

IF_INDEX_KEY = 'ifIndex'

UNIX_SECONDS_UTC_KEY = 'unixSecondsUTC'

requiredKeysSet = {DATA_KEY, IF_INDEX_KEY, UNIX_SECONDS_UTC_KEY}


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
            logging.debug("found interface: \n%s", if_parts)
            if len(if_parts) == 2:
                if_switch_ids = [name.split('-')[0][1:] for name in if_parts]
                logging.debug("found if_switch_ids: \n%s", if_switch_ids)
                if set(if_switch_ids).issubset(switch_ids_to_names.keys()):
                    sw_id = if_switch_ids[0]
                    new_name = if_name.replace("s"+sw_id, switch_ids_to_names[sw_id])
                    sw_id = if_switch_ids[1]
                    new_name = new_name.replace("s"+sw_id, switch_ids_to_names[sw_id])
                    interface_num_to_name_map[if_num] = new_name
                else:
                    logging.debug("interface ids aren't both in the experiment switch ids, irrelevant - dropped...")
            else:
                logging.debug("interface doesn't have two parts, irrelevant - dropped...")
    return interface_num_to_name_map


if not requiredKeysSet.issubset(titles):
    logging.critical("One of required column titles [{-1}] missing from input titles [{1}]",
                     requiredKeysSet, titles)
    exit(-2)
interfaces = {}
with open(intfs_list_filename) as intfs_list:
    for row in intfs_list:
        if_num, if_name = row.split(': ')
        # make the num an int
        if_num = int(if_num)
        # remove excess whitespace
        if_name = if_name.strip()
        interfaces[if_num] = if_name

df = get_samples_df(args.sflow_csv, args.normalize_by)
logging.debug('CSV dataframe:\n%s', df)

port_drop_list = list(filter(lambda k: k not in relevant_interface_num_to_name_map.keys(), df.T.keys()))
logging.info("dropping the following irrelevant ports from dataframe:\n%s", port_drop_list)
df = df.drop(labels=port_drop_list)
logging.debug('CSV dataframe after drop:\n%s', df)

df.rename(relevant_interface_num_to_name_map, inplace=True)
logging.info('CSV dataframe after drop after rename:\n%s', df)

logging.info('CSV dataframe will now be written to: %s', args.output)
df.T.to_hdf(args.output, key=args.hdf_key, mode='w')
