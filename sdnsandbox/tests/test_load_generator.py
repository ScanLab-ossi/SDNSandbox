import json
from unittest import TestCase

from sdnsandbox.load_generator import DitgImixLoadGenerator, LoadGeneratorFactory, Protocol, DITGConfig


class TestLoadGenerator(TestCase):
    def test_create_ditg_load_generator_from_example_config(self):
        generator_conf = json.loads('''{
                                        "type": "DITG",
                                        "protocol": "UDP",
                                        "periods": 1200,
                                        "period_duration_seconds": 30,
                                        "pps_base_level": 150,
                                        "pps_amplitude": 100,
                                        "pps_wavelength": 25
                                      }''')
        generator = LoadGeneratorFactory().create(generator_conf)
        self.assertIsInstance(generator, DitgImixLoadGenerator)
        self.assertEqual(Protocol.UDP, generator.config.protocol)
        self.assertEqual(1200, generator.config.periods)
        self.assertEqual(30, generator.config.period_duration_seconds)
        self.assertEqual(150, generator.config.pps_base_level)
        self.assertEqual(100, generator.config.pps_amplitude)
        self.assertEqual(25, generator.config.pps_wavelength)
        self.assertEqual(DITGConfig.warmup_seconds, generator.config.warmup_seconds)

    def test_raise_exception_create_ditg_load_generator_unknown_protocol(self):
        generator_conf = json.loads('''{
                                        "type": "DITG",
                                        "protocol": "MYP"
                                        }''')
        with self.assertRaises(ValueError) as cm:
            LoadGeneratorFactory().create(generator_conf)
        self.assertEqual(str(cm.exception), 'Unknown protocol=MYP')

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
    # def test_calculate_destination(self):
    #     self.fail()
    #
    # def test_calculate_send_opts(self):
    #     self.fail()
