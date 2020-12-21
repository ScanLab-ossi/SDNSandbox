from unittest import TestCase
import pandas as pd

from sdnsandbox.processor import IQRProcessor


class TestProcessor(TestCase):
    samples = {1607902307: {'mean41': 4247.0, 'mean43': 6394.0, 'mean45': 3973.0},
               1607902308: {'mean41': 15705.0, 'mean43': 17189.0, 'mean45': 14173.0},
               1607902309: {'mean41': 23667.0, 'mean43': 20479.0, 'mean45': 26415.0},
               1607902310: {'mean41': 33740.0, 'mean43': 22100.0, 'mean45': 35928.0},
               1607902311: {'mean41': 50265.0, 'mean43': 24906.0, 'mean45': 51948.0}}
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

    def test_get_iqr_results(self):
        self.assertEqual(self.expected_iqr_results,
                         IQRProcessor.get_iqr_results(sampling_df=pd.DataFrame(self.samples)))
