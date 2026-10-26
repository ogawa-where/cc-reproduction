import os
import tempfile
import unittest

from fileindex.scan import Entry, ScanError, extension, scan


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "sub"))
        with open(os.path.join(self.root, "b.txt"), "w") as fh:
            fh.write("12345")
        with open(os.path.join(self.root, "sub", "a.py"), "w") as fh:
            fh.write("x")

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_lists_files_sorted(self):
        self.assertEqual(scan(self.root), [Entry("b.txt", 5), Entry("sub/a.py", 1)])

    def test_scan_rejects_missing_root(self):
        with self.assertRaises(ScanError):
            scan(os.path.join(self.root, "missing"))

    def test_extension(self):
        self.assertEqual(extension("sub/a.py"), "py")
        self.assertIsNone(extension("Makefile"))


if __name__ == "__main__":
    unittest.main()
