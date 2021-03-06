import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from os import makedirs
from typing import List, Any, Dict, Type, Optional
import pandas as pd
from scipy.stats import iqr
from dacite import from_dict
from os.path import join as pj
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')

logger = logging.getLogger(__name__)


class Processor(ABC):
    @abstractmethod
    def process(self, sampling_df: pd.DataFrame, output_path: str):
        pass


@dataclass
class IQRProcessor(Processor):
    iqr_filename: str = 'iqr.json'

    def process(self, sampling_df: pd.DataFrame, output_path: str):
        results = self.get_iqr_results(sampling_df)
        full_path = pj(output_path, self.iqr_filename)
        self.dump_results(full_path, results)

    @staticmethod
    def dump_results(output_path, results):
        logger.info("Dumping IQR results to " + output_path)
        logger.debug("JSON will be created from: %s", str(results))
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)

    @staticmethod
    def get_iqr_results(sampling_df):
        logger.info("Creating IQR results")
        results = {
            'total_iqr':
                IQRProcessor.get_iqr(sampling_df.to_numpy(),
                                     'IQR for all readings'),
            'second_means_iqr':
                IQRProcessor.get_iqr(sampling_df.mean(axis=1).to_numpy(),
                                     'IQR for means of all seconds (mean of all readings per second)'),
            'port_means_iqr':
                IQRProcessor.get_iqr(sampling_df.mean(axis=0).to_numpy(),
                                     'IQR for port means (mean of all the readings a port had)')
        }
        logger.debug("IQR results are: %s", str(results))
        return results

    @staticmethod
    def get_iqr(values, description: str):
        iqr_res = iqr(values)
        result = {'result': iqr_res,
                  'instances_for_calc': values.size,
                  'description': description}
        logger.info(result['description'] + " is " + str(result['result']))
        return result


@dataclass
class PlottingProcessor(Processor):
    plots_dirname: str = 'plots'
    xlabel: str = 'Time'
    ylabel: str = 'MB/s'
    filename_format: str = "link_load_{}.png"

    def process(self, sampling_df: pd.DataFrame, output_path: str, max_x: int = -1):
        plots_dir = pj(output_path, self.plots_dirname)
        logger.info("Creating directory " + plots_dir + " for plots")
        makedirs(plots_dir, exist_ok=True)
        # this is needed for proper time-series plots
        pd.plotting.register_matplotlib_converters()
        for column in sampling_df.keys():
            logger.info("Plotting samples for port " + str(column))
            sampling_df[column][:max_x].plot()
            plt.xlabel(self.xlabel)
            plt.ylabel(self.ylabel)
            plt.tight_layout()
            filename = pj(plots_dir, self.filename_format.format(column))
            logger.info("Saving plot to " + filename)
            plt.savefig(filename)
            plt.close()
        logger.info("Done plotting @ " + plots_dir)


class ProcessorsFactory:
    types = {'IQR': IQRProcessor,
             'Plotting': PlottingProcessor}  # type: Dict[str, Type[Processor]]

    @classmethod
    def create(cls, processors_config: List[Dict[str, Any]], types: Optional[Dict[str, Type[Processor]]] = None)\
            -> List[Processor]:
        if types is None:
            types = cls.types
        processors = []
        for processor_config in processors_config:
            processor = from_dict(types[processor_config['type']], processor_config)
            processors.append(processor)
        return processors
