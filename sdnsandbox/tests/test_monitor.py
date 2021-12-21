import json
import unittest
from os.path import abspath, dirname, join as pj
from timeit import repeat as timeit
import pandas as pd
from numpy import datetime64

from sdnsandbox.monitor import SFlowMonitor, MonitorFactory


class MonitorTestCase(unittest.TestCase):
    expected_interfaces = {41: 'mean41',
                           43: 'mean43',
                           45: 'mean45'}
    full_interfaces = {i: 'mean'+str(i) for i in range(2, 80)}

    @classmethod
    def setUpClass(cls):
        sflow_csv_path = pj(dirname(abspath(__file__)), "sflow.csv")
        cls.sflow_csv = open(sflow_csv_path)
        big_sflow_csv_path = pj(dirname(abspath(__file__)), "big_sflow.csv")
        cls.big_sflow_csv = open(big_sflow_csv_path)
        cls.keys = [SFlowMonitor.sflow_time_key,
                    SFlowMonitor.sflow_intf_index_key,
                    "data_key"]
        expected_samples = {1607902308: {'mean41': 11458.0, 'mean43': 10795.0, 'mean45': 10200.0},
                            1607902309: {'mean41': 7962.0, 'mean43': 3290.0, 'mean45': 12242.0},
                            1607902310: {'mean41': 10073.0, 'mean43': 1621.0, 'mean45': 9513.0},
                            1607902311: {'mean41': 16525.0, 'mean43': 2806.0, 'mean45': 16020.0}}
        expected_normalized_samples = {1607902308: {'mean41': 11.458, 'mean43': 10.795, 'mean45': 10.200},
                                       1607902309: {'mean41': 7.962, 'mean43': 3.290, 'mean45': 12.242},
                                       1607902310: {'mean41': 10.073, 'mean43': 1.621, 'mean45': 9.513},
                                       1607902311: {'mean41': 16.525, 'mean43': 2.806, 'mean45': 16.020}}
        cls.expected_samples = pd.DataFrame.from_dict(expected_samples, orient='index')
        cls.expected_samples.rename_axis(cls.keys[0], inplace=True)
        cls.expected_samples.rename_axis(cls.keys[1], axis=1, inplace=True)
        cls.expected_samples.index = cls.expected_samples.index.map(lambda time:
                                                                    datetime64(time, 's'))
        cls.expected_normalized_samples = pd.DataFrame.from_dict(expected_normalized_samples, orient='index')
        cls.expected_normalized_samples.rename_axis(cls.keys[0], inplace=True)
        cls.expected_normalized_samples.rename_axis(cls.keys[1], axis=1, inplace=True)
        cls.expected_normalized_samples.index = cls.expected_normalized_samples.index.map(lambda time:
                                                                                          datetime64(time, 's'))

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
        except (AssertionError, ValueError, TypeError) as e:
            print(e)
            print('df1:')
            print(df1)
            print('df2:')
            print(df2)
            return False

    def test_create_sflow_monitor_from_example_config(self):
        monitor_conf = json.loads('''{
                        "type": "sflow",
                        "data_key": "ifInOctets",
                        "normalize_by": 1048576,
                        "csv_filename": "sflow.csv",
                        "sflowtool_cmd": "git"
                      }''')
        monitor = MonitorFactory().create(monitor_conf)
        self.assertIsInstance(monitor, SFlowMonitor)
        self.assertEqual("ifInOctets", monitor.sflow_keys_to_monitor[2])
        self.assertEqual(1048576, monitor.config.normalize_by)
        self.assertEqual("sflow.csv", monitor.config.csv_filename)
        self.assertEqual("git", monitor.config.sflowtool_cmd)

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
