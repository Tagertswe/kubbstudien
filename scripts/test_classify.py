"""Unit tests for scripts/classify.py. Run: python3 -m unittest discover -s scripts"""
import unittest

import classify


class InRanges(unittest.TestCase):
    TABLE = {"2018": [(44, 47)], "2018-J": [(1, 3), (5, 6)]}

    def test_own_and_guest_refs_use_separate_tables(self):
        self.assertTrue(classify.in_ranges("2018-044", self.TABLE))
        self.assertFalse(classify.in_ranges("2018-003", self.TABLE))
        self.assertTrue(classify.in_ranges("2018-J003", self.TABLE))
        self.assertFalse(classify.in_ranges("2018-J044", self.TABLE))

    def test_ranges_are_inclusive_and_gaps_are_respected(self):
        self.assertTrue(classify.in_ranges("2018-J005", self.TABLE))
        self.assertFalse(classify.in_ranges("2018-J004", self.TABLE))
        self.assertFalse(classify.in_ranges("2019-J001", self.TABLE))


if __name__ == "__main__":
    unittest.main()
