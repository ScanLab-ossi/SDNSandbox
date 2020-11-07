from unittest import TestCase
from sdnsandbox.util import calculate_geodesic_latency, _calculate_latency


class TestUtil(TestCase):
    def test_calculate_geodesic_latency_zero_distance(self):
        latency = calculate_geodesic_latency(0, 0, 0, 0)
        self.assertEqual(latency, 0.0)

    def test_calculate_geodesic_latency_microsecond_accuracy(self):
        latency = calculate_geodesic_latency(0, 0, 10, 10)
        self.assertAlmostEqual(latency, 7.556, delta=0.001)

    def test___calculate_latency_zero_distance(self):
        latency = _calculate_latency(0, 0, 0, 0)
        self.assertEqual(latency, 0.0)

    def test___calculate_latency_microsecond_accuracy(self):
        latency = _calculate_latency(0, 0, 10, 10)
        self.assertAlmostEqual(latency, 7.581, delta=0.001)
