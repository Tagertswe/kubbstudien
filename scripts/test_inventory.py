"""Unit tests for scripts/inventory.py. Run: python3 -m unittest discover -s scripts"""
import unittest

import inventory


class Dedupe(unittest.TestCase):
    def test_keeps_the_first_row_per_id(self):
        rows = [{"id": 1, "album": "Camera"}, {"id": 2, "album": "Camera"}, {"id": 1, "album": "Photos from 2025"}]
        self.assertEqual(inventory.dedupe(rows), [{"id": 1, "album": "Camera"}, {"id": 2, "album": "Camera"}])

    def test_empty(self):
        self.assertEqual(inventory.dedupe([]), [])


class Number(unittest.TestCase):
    def row(self, id, time, source="own", date="2018-06-22"):
        return {"id": id, "date": date, "time": time, "source": source}

    def test_guest_files_do_not_shift_own_refs(self):
        own = [self.row(1, "11:00:00"), self.row(2, "19:00:00")]
        before = {r["id"]: r["ref"] for r in inventory.number([dict(r) for r in own])}
        mixed = inventory.number(own + [self.row(9, "12:00:00", "guest")])
        after = {r["id"]: r["ref"] for r in mixed}
        self.assertEqual(before, {1: "2018-001", 2: "2018-002"})
        self.assertEqual(after, {1: "2018-001", 2: "2018-002", 9: "2018-J001"})

    def test_numbering_restarts_each_year_and_follows_time(self):
        rows = inventory.number([self.row(1, "19:00:00", "guest"), self.row(2, "18:00:00", "guest"),
                                 self.row(3, "18:00:00", "guest", date="2014-06-20")])
        self.assertEqual({r["id"]: r["ref"] for r in rows}, {2: "2018-J001", 1: "2018-J002", 3: "2014-J001"})


if __name__ == "__main__":
    unittest.main()
