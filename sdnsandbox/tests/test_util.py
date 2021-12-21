import io
from unittest import TestCase
from sdnsandbox.util import countdown, \
    calculate_geodesic_latency, \
    calculate_manual_geodesic_latency


class TestUtil(TestCase):
    def test_calculate_geodesic_latency_zero_distance(self):
        latency = calculate_geodesic_latency(0, 0, 0, 0)
        self.assertEqual(0.0, latency)

    def test_calculate_geodesic_latency_microsecond_accuracy(self):
        latency = calculate_geodesic_latency(0, 0, 10, 10)
        self.assertAlmostEqual(7.556, latency, delta=0.001)

    def test_calculate_manual_geodesic_latency_zero_distance(self):
        latency = calculate_manual_geodesic_latency(0, 0, 0, 0)
        self.assertEqual(0.0, latency)

    def test_calculate_manual_geodesic_latency_microsecond_accuracy(self):
        latency = calculate_manual_geodesic_latency(0, 0, 10, 10)
        self.assertAlmostEqual(7.581, latency, delta=0.001)

    def test_countdown(self):
        output = io.StringIO()
        countdown(output.write, 3, delay_func=lambda a: a)
        self.assertEqual('00:0300:0200:01Done!', output.getvalue())
