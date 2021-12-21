from dataclasses import asdict
from unittest import TestCase

from sdnsandbox.network import Interface
from sdnsandbox.runner import Runner, InterfaceTranslation


class TestRunner(TestCase):
    interfaces = {3: Interface(num=3, name='s3-eth2@s0-eth3', net_meaning='three-eth2@zero-eth3')}

    def test_get_interfaces_naming_num_to_string(self):
        expected = {3: str(self.interfaces[3].num)}
        res = Runner.get_interfaces_naming(InterfaceTranslation.NUM_TO_STRING, self.interfaces)
        self.assertEqual(expected, res)

    def test_get_interfaces_naming_to_names(self):
        expected = {3: str(self.interfaces[3].name)}
        res = Runner.get_interfaces_naming(InterfaceTranslation.TRANSLATE_TO_NAMES, self.interfaces)
        self.assertEqual(expected, res)

    def test_get_interfaces_naming_to_meanings(self):
        expected = {3: str(self.interfaces[3].net_meaning)}
        res = Runner.get_interfaces_naming(InterfaceTranslation.TRANSLATE_TO_MEANINGS, self.interfaces)
        self.assertEqual(expected, res)
