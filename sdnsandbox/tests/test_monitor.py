import json
import unittest
from os.path import abspath, dirname, join as pj
from timeit import repeat as timeit

import pandas as pd

from sdnsandbox.monitor import SFlowMonitor, MonitorFactory


class MonitorTestCase(unittest.TestCase):
    sflow_csv = None
    expected_samples = {1607902307: {'of41': 4247, 'of43': 6394, 'of45': 3973},
                        1607902308: {'of41': 15705, 'of43': 17189, 'of45': 14173},
                        1607902309: {'of41': 23667, 'of43': 20479, 'of45': 26415},
                        1607902310: {'of41': 33740, 'of43': 22100, 'of45': 35928},
                        1607902311: {'of41': 50265, 'of43': 24906, 'of45': 51948}}
    expected_normalized_samples = {1607902307: {'of41': 4.247, 'of43': 6.394, 'of45': 3.973},
                                   1607902308: {'of41': 15.705, 'of43': 17.189, 'of45': 14.173},
                                   1607902309: {'of41': 23.667, 'of43': 20.479, 'of45': 26.415},
                                   1607902310: {'of41': 33.740, 'of43': 22.100, 'of45': 35.928},
                                   1607902311: {'of41': 50.265, 'of43': 24.906, 'of45': 51.948}}
    expected_interfaces = {'41': 'of41', '43': 'of43', '45': 'of45'}
    full_interfaces = {str(i): 'of'+str(i) for i in range(2, 80)}

    @classmethod
    def setUpClass(cls):
        sflow_csv_path = pj(dirname(abspath(__file__)), "sflow.csv")
        cls.sflow_csv = open(sflow_csv_path)
        big_sflow_csv_path = pj(dirname(abspath(__file__)), "big_sflow.csv")
        cls.big_sflow_csv = open(big_sflow_csv_path)
        cls.keys = [SFlowMonitor.sflow_time_key,
                    SFlowMonitor.sflow_intf_index_key,
                    "data_key"]
        cls.expected_samples = pd.DataFrame.from_dict(cls.expected_samples, orient='index')
        cls.expected_samples.rename_axis(cls.keys[0], inplace=True)
        cls.expected_samples.rename_axis(cls.keys[1], axis=1, inplace=True)
        cls.expected_normalized_samples = pd.DataFrame.from_dict(cls.expected_normalized_samples, orient='index')
        cls.expected_normalized_samples.rename_axis(cls.keys[0], inplace=True)
        cls.expected_normalized_samples.rename_axis(cls.keys[1], axis=1, inplace=True)

    def setUp(self):
        self.sflow_csv.seek(0)

    @classmethod
    def tearDownClass(cls):
        cls.sflow_csv.close()

    @staticmethod
    def are_dfs_equal(df1, df2):
        from pandas.util.testing import assert_frame_equal
        try:
            assert_frame_equal(df1, df2, check_names=True)
            return True
        except (AssertionError, ValueError, TypeError):
            return False

    def test_create_sflow_monitor_from_example_config(self):
        monitor_conf = json.loads('''{
                        "type": "sflow",
                        "data_key": "ifInOctets",
                        "normalize_by": 1048576,
                        "csv_filename": "sflow.csv",
                        "interfaces_filename": "interfaces.json",
                        "sflowtool_cmd": "git"
                      }''')
        monitor = MonitorFactory().create(monitor_conf)
        self.assertIsInstance(monitor, SFlowMonitor)
        self.assertEqual("ifInOctets", monitor.sflow_keys_to_monitor[2])
        self.assertEqual(1048576, monitor.config.normalize_by)
        self.assertEqual("sflow.csv", monitor.config.csv_filename)
        self.assertEqual("interfaces.json", monitor.config.interfaces_filename)

    def test_get_samples_no_normalization_pandas(self):
        samples_df = SFlowMonitor.get_samples_pandas(self.sflow_csv,
                                                     self.keys,
                                                     self.expected_interfaces,
                                                     normalize_by=None)
        self.assertTrue(self.are_dfs_equal(self.expected_samples, samples_df))

    def test_get_samples_with_normalization_pandas(self):
        samples_df = SFlowMonitor.get_samples_pandas(self.sflow_csv,
                                                     self.keys,
                                                     self.expected_interfaces,
                                                     normalize_by=1000)
        self.assertTrue(self.are_dfs_equal(self.expected_normalized_samples, samples_df))

    def test_get_samples_no_normalization(self):
        samples_df = SFlowMonitor.get_samples(self.sflow_csv,
                                              self.keys,
                                              self.expected_interfaces,
                                              normalize_by=None)
        self.assertTrue(self.are_dfs_equal(self.expected_samples, samples_df))

    def test_get_samples_with_normalization(self):
        samples_df = SFlowMonitor.get_samples(self.sflow_csv,
                                              self.keys,
                                              self.expected_interfaces,
                                              normalize_by=1000)
        self.assertTrue(self.are_dfs_equal(self.expected_normalized_samples, samples_df))

    def test_compare_both_versions(self, repetitions=10):
        time_res = timeit(lambda: SFlowMonitor.get_samples(self.big_sflow_csv,
                                                           self.keys,
                                                           self.full_interfaces,
                                                           normalize_by=1000),
                          setup=lambda: self.big_sflow_csv.seek(0),
                          number=1,
                          repeat=repetitions)
        self.big_sflow_csv.seek(0)
        manual_samples_df = SFlowMonitor.get_samples(self.big_sflow_csv,
                                                     self.keys,
                                                     self.full_interfaces,
                                                     normalize_by=1000)
        print("manual took= {:.10f} [sec]".format(sum(time_res)))

        time_res = timeit(lambda: SFlowMonitor.get_samples_pandas(self.big_sflow_csv,
                                                                  self.keys,
                                                                  self.full_interfaces,
                                                                  normalize_by=1000),
                          setup=lambda: self.big_sflow_csv.seek(0),
                          number=1,
                          repeat=repetitions)
        self.big_sflow_csv.seek(0)
        pandas_samples_df = SFlowMonitor.get_samples_pandas(self.big_sflow_csv,
                                                            self.keys,
                                                            self.full_interfaces,
                                                            normalize_by=1000)
        print("pandas took= {:.10f} [sec]".format(sum(time_res)))
        self.assertTrue(self.are_dfs_equal(manual_samples_df, pandas_samples_df))


if __name__ == '__main__':
    unittest.main()
