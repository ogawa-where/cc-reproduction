import unittest

from fileindex.index import NO_EXTENSION, by_extension, counts, largest
from fileindex.scan import Entry


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.entries = [Entry("a.py", 3), Entry("b.py", 9), Entry("Makefile", 1)]

    def test_by_extension(self):
        groups = by_extension(self.entries)
        self.assertEqual(sorted(groups), [NO_EXTENSION, "py"])
        self.assertEqual(len(groups["py"]), 2)

    def test_counts(self):
        self.assertEqual(counts(self.entries), {"py": 2, NO_EXTENSION: 1})

    def test_largest(self):
        self.assertEqual(largest(self.entries), Entry("b.py", 9))
        self.assertIsNone(largest([]))


if __name__ == "__main__":
    unittest.main()
