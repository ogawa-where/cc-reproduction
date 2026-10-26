import unittest

from fileindex.query import find_all_by_name, find_by_name
from fileindex.scan import Entry


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.entries = [Entry("a/x.txt", 1), Entry("b/x.txt", 2), Entry("y.txt", 3)]

    def test_find_by_name(self):
        self.assertEqual(find_by_name(self.entries, "x.txt"), Entry("a/x.txt", 1))
        self.assertIsNone(find_by_name(self.entries, "z.txt"))

    def test_find_all_by_name(self):
        self.assertEqual(len(find_all_by_name(self.entries, "x.txt")), 2)


if __name__ == "__main__":
    unittest.main()
