import json
from unittest import TestCase

from sdnsandbox.load_generator import DitgImixLoadGenerator, LoadGeneratorFactory, Protocol, DITGConfig, NpingConfig, \
    NpingUDPImixLoadGenerator, StaticDeltaDestinationCalculator, RoundRobinDestinationCalculator


class TestLoadGenerator(TestCase):
    def test_create_ditg_imix_udp_load_generator_from_example_config(self):
        generator_conf = json.loads('''{
                                        "type": "DITG-IMIX",
                                        "disable_cmd_ensure": true,
                                        "protocol": "UDP",
                                        "periods": 1200,
                                        "period_duration_seconds": 30,
                                        "pps_base_level": 150,
                                        "pps_amplitude": 100,
                                        "pps_wavelength": 25
                                      }''')
        generator = LoadGeneratorFactory().create(generator_conf)
        self.assertIsInstance(generator, DitgImixLoadGenerator)
        self.assertEqual(True, generator.config.disable_cmd_ensure)
        self.assertEqual(Protocol.UDP, generator.config.protocol)
        self.assertEqual(1200, generator.config.periods)
        self.assertEqual(30, generator.config.period_duration_seconds)
        self.assertEqual(150, generator.config.pps_base_level)
        self.assertEqual(100, generator.config.pps_amplitude)
        self.assertEqual(25, generator.config.pps_wavelength)
        self.assertIsInstance(NpingConfig.destination_calculator, StaticDeltaDestinationCalculator)
        self.assertEqual(DITGConfig.warmup_seconds, generator.config.warmup_seconds)

    def test_create_nping_load_generator_from_example_config(self):
        generator_conf = json.loads('''{
                                        "type": "NPING-UDP-IMIX",
                                        "disable_cmd_ensure": true,
                                        "periods": 1200,
                                        "period_duration_seconds": 30,
                                        "pps_base_level": 150,
                                        "pps_amplitude": 100,
                                        "pps_wavelength": 25
                                      }''')
        generator = LoadGeneratorFactory().create(generator_conf)
        self.assertIsInstance(generator, NpingUDPImixLoadGenerator)
        self.assertEqual(True, generator.config.disable_cmd_ensure)
        self.assertEqual(1200, generator.config.periods)
        self.assertEqual(30, generator.config.period_duration_seconds)
        self.assertEqual(150, generator.config.pps_base_level)
        self.assertEqual(100, generator.config.pps_amplitude)
        self.assertEqual(25, generator.config.pps_wavelength)
        self.assertEqual(NpingConfig.listen_port, generator.config.listen_port)
        self.assertIsInstance(NpingConfig.destination_calculator, StaticDeltaDestinationCalculator)
        self.assertEqual(NpingConfig.verbosity_level, generator.config.verbosity_level)

    def test_create_nping_load_generator_with_static_delta_dest_calc(self):
        generator_conf = json.loads('''{
                                        "type": "NPING-UDP-IMIX",
                                        "disable_cmd_ensure": true,
                                        "periods": 1200,
                                        "period_duration_seconds": 30,
                                        "pps_base_level": 150,
                                        "pps_amplitude": 100,
                                        "pps_wavelength": 25,
                                        "destination_calculator": {
                                            "strategy": "static_delta",
                                            "delta": "6"
                                            } 
                                      }''')
        generator = LoadGeneratorFactory().create(generator_conf)
        self.assertIsInstance(generator, NpingUDPImixLoadGenerator)
        self.assertIsInstance(generator.config.destination_calculator, StaticDeltaDestinationCalculator)
        self.assertEqual(generator.config.destination_calculator.delta, 6)

    def test_create_nping_load_generator_with_round_robin_dest_calc(self):
        generator_conf = json.loads('''{
                                        "type": "NPING-UDP-IMIX",
                                        "disable_cmd_ensure": true,
                                        "periods": 1200,
                                        "period_duration_seconds": 30,
                                        "pps_base_level": 150,
                                        "pps_amplitude": 100,
                                        "pps_wavelength": 25,
                                        "destination_calculator": {"strategy": "round_robin"} 
                                      }''')
        generator = LoadGeneratorFactory().create(generator_conf)
        self.assertIsInstance(generator, NpingUDPImixLoadGenerator)
        self.assertIsInstance(generator.config.destination_calculator, RoundRobinDestinationCalculator)

    def test_raise_exception_create_ditg_load_generator_unknown_protocol(self):
        generator_conf = json.loads('''{
                                        "type": "DITG-IMIX",
                                        "protocol": "MYP"
                                        }''')
        with self.assertRaises(ValueError) as cm:
            LoadGeneratorFactory().create(generator_conf)
        self.assertEqual(str(cm.exception), 'Unknown protocol=MYP')

    def test_round_robin_dest_calc(self):
        host_addresses = ['10.0.0.1', '10.0.0.2', '10.0.0.3']
        host_index = 1
        dest_calc = RoundRobinDestinationCalculator()
        expected_dests = ['10.0.0.3', '10.0.0.1', '10.0.0.3', '10.0.0.1', '10.0.0.3', '10.0.0.1']
        for period in range(6):
            self.assertEqual(expected_dests[period], dest_calc.calculate_destination(period, host_index, host_addresses))

    def test_static_delta_dest_calc(self):
        host_addresses = ['10.0.0.1', '10.0.0.2', '10.0.0.3']
        host_index = 1
        dest_calc = StaticDeltaDestinationCalculator()
        for period in range(6):
            self.assertEqual('10.0.0.3', dest_calc.calculate_destination(period, host_index, host_addresses))
        dest_calc = StaticDeltaDestinationCalculator(1)
        for period in range(6):
            self.assertEqual('10.0.0.1', dest_calc.calculate_destination(period, host_index, host_addresses))
        dest_calc = StaticDeltaDestinationCalculator(6)
        for period in range(6):
            self.assertEqual('10.0.0.3', dest_calc.calculate_destination(period, host_index, host_addresses))
    # TODO: complete tests
    # def test_start_receivers(self):
    #     self.fail()
    #
    # def test_run_senders(self):
    #     self.fail()
    #
    # def test_run_host_senders(self):
    #     self.fail()
    #
    # def test_stop_receivers(self):
    #     self.fail()
    #
    # def test_calculate_send_opts(self):
    #     self.fail()
