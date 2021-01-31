import argparse
import csv
import logging
import sys
from collections import namedtuple
from contextlib import contextmanager
from os import chdir, walk, getcwd
from os.path import join as pj, isfile
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile
import numpy as np
from matplotlib.pyplot import subplots, savefig

from sdnsandbox.topology import ITZTopologyCreator

GRAPHML_SUFFIX = '.graphml'

Dataset = namedtuple('Dataset', ['save_as', 'url'])
Topology = namedtuple('Topology', ['name', 'size'])


def setup_logging(is_debug=False):
    root_logger = logging.getLogger()
    if is_debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s->%(name)s-%(levelname)s: %(message)s')
    sh.setFormatter(formatter)
    root_logger.addHandler(sh)


@contextmanager
def switch_cwd(tmp_dir):
    init_cwd = getcwd()
    try:
        logging.info('Changing current working directory from=%s to= %s', init_cwd, tmp_dir)
        chdir(tmp_dir)
        yield init_cwd
    finally:
        logging.info('Changing current working directory back to=%s', init_cwd)
        chdir(init_cwd)


def download_zip(url, save_as):
    logging.info('Downloading dataset zip at %s', url)
    with urlopen(url) as response:
        logging.info('Saving dataset zip at %s', save_as)
        with open(save_as, 'wb') as out_file:
            out_file.write(response.read())


def extract_zip(temp_dir, dataset, keep_zip):
    with switch_cwd(temp_dir) as curr_cwd:
        if keep_zip:
            zip_path = pj(curr_cwd, dataset.save_as)
        else:
            download_zip(dataset.url, dataset.save_as)
            zip_path = dataset.save_as
        logging.info('Extracting dataset zip at %s', temp_dir)
        ZipFile(zip_path).extractall()


def process_dataset(dataset, keep_zip):
    logging.info('Processing dataset zip at %s', dataset.url)
    if keep_zip:
        if isfile(dataset.save_as):
            logging.info("Found existing zip file, will use it for processing")
        else:
            logging.info("Did not find existing zip file, will download for processing")
            download_zip(dataset.url, dataset.save_as)
    topologies = []
    with TemporaryDirectory() as tmp_dir:
        extract_zip(tmp_dir, dataset, keep_zip)

        for folder, _, files in walk(tmp_dir):
            for filename in files:
                if filename.endswith(GRAPHML_SUFFIX):
                    graphml_path = pj(folder, filename)
                    logging.info('Processing file %s', graphml_path)
                    try:
                        with open(graphml_path) as f:
                            graphml = f.read()
                            topo_size = len(ITZTopologyCreator.extract_switches_and_links_from_graphml(graphml)[0])
                            topologies.append(Topology(filename.split(GRAPHML_SUFFIX)[0], topo_size))
                    except RuntimeError:
                        logging.error('Exception raised during processing of file=%s Skipping!', graphml_path)
    logging.info("Found a total of %d topologies, with an average size of %.2f",
                 len(topologies),
                 sum([t.size for t in topologies])/float(len(topologies)))
    return topologies


def plot_sizes(bins, sizes, plot_title, plot_filename):
    bin_ranges = [(bins[i], bins[i + 1]) for i in range(len(bins) - 1)]
    hist, bin_edges = np.histogram(sizes, bins=bins)
    _, ax = subplots()
    ax.bar(range(len(hist)), hist, width=1, align='center',
           tick_label=['{} - {}'.format(r[0], r[1]) for r in bin_ranges])
    ax.set_title(plot_title)
    # add bar values
    for i, v in enumerate(hist):
        ax.text(i + .25, v + 3, str(v), color='black', fontweight='bold')
    logging.info('Saving sizes plot to %s', plot_filename)
    savefig(plot_filename)


def save_csv(topologies, csv_filename):
    logging.info('Saving CSV of found topologies to %s', csv_filename)
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=Topology._fields)
        writer.writeheader()
        # writer.writerows(topologies)
        writer.writerows(map(Topology._asdict, topologies))


def parse_arguments():
    parser = argparse.ArgumentParser(prog="process_itz_archive",
                                     description='Process topologies archive - save sizes plot and csv')
    parser.add_argument('--zip-archive-name', default='itz_dataset.zip')
    parser.add_argument('--zip-archive-url', default='http://www.topology-zoo.org/files/archive.zip')
    parser.add_argument("-k", "--keep-zip", action='store_true', help="Keep the dataset zip for future processing")
    parser.add_argument('-b', '--bins', nargs='+', default=[0, 50, 100, 250, 1000],
                        help='bins to be used for histogram plot')
    parser.add_argument("--plot-title", default='Network Sizes Distribution in ITZ Dataset')
    parser.add_argument("--plot-filename", default="itz_sizes.png")
    parser.add_argument('-c', '--csv-filename', default='topology_dataset.csv')
    parser.add_argument("-d", "--debug", action="store_true", help="Set log verbosity to debug level")
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    setup_logging(args.debug)
    ds = Dataset(args.zip_archive_name, args.zip_archive_url)
    topologies = process_dataset(ds, args.keep_zip)
    data = [topo.size for topo in topologies]
    plot_sizes(args.bins, data, args.plot_title, args.plot_filename)
    save_csv(topologies, args.csv_filename)
