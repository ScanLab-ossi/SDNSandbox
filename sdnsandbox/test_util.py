import io
from unittest import TestCase
from sdnsandbox.util import countdown, calculate_geodesic_latency, _calculate_latency, get_interfaces

ip_a_output = '''1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: s0-eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc htb master ovs-system state UP group default qlen 1000
    link/ether 16:47:ba:01:0b:05 brd ff:ff:ff:ff:ff:ff link-netnsid 1
3: s3-eth2@s0-eth3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc htb master ovs-system state UP group default qlen 1000
    link/ether 86:57:62:6c:06:1b brd ff:ff:ff:ff:ff:ff
'''

interfaces = {'1': 'lo',
              '2': 's0-eth1',
              '3': 's3-eth2@s0-eth3'}


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

    def test_countdown(self):
        output = io.StringIO()
        countdown(output.write, 3, delay_func=lambda a: a)
        self.assertEqual(output.getvalue(), '00:0300:0200:01Done!')

    def test_get_interfaces(self):
        res = get_interfaces(ip_a_getter=lambda: ip_a_output)
        self.assertEqual(res, interfaces)
