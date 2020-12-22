from tempfile import TemporaryDirectory
from unittest import TestCase
import pandas as pd
from os.path import join as pj, isfile, isdir
import os
from numpy import datetime64

from sdnsandbox.processor import IQRProcessor, PlottingProcessor


class TestProcessor(TestCase):
    expected_iqr_results = {
        'port_means_iqr': {'description': 'IQR for port means (mean of all the readings a port had)',
                           'instances_for_calc': 3,
                           'result': 4136.9000000000015},
        'second_means_iqr': {'description': 'IQR for means of all seconds (mean of '
                                            'all readings per second)',
                             'instances_for_calc': 5,
                             'result': 14900.333333333332},
        'total_iqr': {'description': 'IQR for all readings',
                      'instances_for_calc': 15,
                      'result': 15138.5}}

    @classmethod
    def setUpClass(cls) -> None:
        cls.sampling_df = pd.DataFrame.from_dict(
            {1607902307: {'mean41': 4247.0, 'mean43': 6394.0, 'mean45': 3973.0},
             1607902308: {'mean41': 15705.0, 'mean43': 17189.0, 'mean45': 14173.0},
             1607902309: {'mean41': 23667.0, 'mean43': 20479.0, 'mean45': 26415.0},
             1607902310: {'mean41': 33740.0, 'mean43': 22100.0, 'mean45': 35928.0},
             1607902311: {'mean41': 50265.0, 'mean43': 24906.0, 'mean45': 51948.0}}, orient='index')
        cls.sampling_df.index = cls.sampling_df.index.map(lambda time:
                                                          datetime64(time, 's'))

    def test_get_iqr_results(self):
        self.assertEqual(self.expected_iqr_results,
                         IQRProcessor.get_iqr_results(sampling_df=self.sampling_df))

    def test_plotting_creates_files(self):
        plots_subdir = 'plots'
        with TemporaryDirectory() as temp_dir:
            print('Using temp dir ', temp_dir)
            processor = PlottingProcessor(plots_dirname=plots_subdir)
            processor.process(sampling_df=self.sampling_df, output_path=temp_dir)
            plots_full_path = pj(temp_dir, plots_subdir)
            self.assertTrue(isdir(plots_full_path))
            filenames = []
            for key in self.sampling_df.keys():
                filename = PlottingProcessor.filename_format.format(key)
                path = pj(plots_full_path, filename)
                self.assertTrue(isfile(path))
                filenames.append(filename)
            self.assertEqual(filenames, os.listdir(plots_full_path))
            from time import sleep
            sleep(30)
