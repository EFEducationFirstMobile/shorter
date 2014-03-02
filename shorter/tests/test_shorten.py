import unittest

from shorter import shorten


class TestShorten(unittest.TestCase):
    def test_int_to_base36(self):
        self.assertEqual(shorten.int_to_base36(1), '1')
        self.assertEqual(shorten.int_to_base36(35), 'z')
        self.assertEqual(shorten.int_to_base36(36), '10')
