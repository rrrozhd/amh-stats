import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

import stats


class StatsTest(unittest.TestCase):
    def run_stats(self, text):
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(text)), redirect_stdout(out):
            code = stats.main(["stats.py"])
        return code, out.getvalue()

    def test_count_and_mean(self):
        self.assertEqual(self.run_stats("1\n2\n3\n6\n"), (0, "count 4\nmean 3\n"))

    def test_blank_lines_ignored(self):
        self.assertEqual(self.run_stats("\n2\n\n4\n"), (0, "count 2\nmean 3\n"))


if __name__ == "__main__":
    unittest.main()
