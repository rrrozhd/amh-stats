import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import stats


def run_main(args, stdin=""):
    """Run stats.main with the given arguments; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(stdin)), redirect_stdout(out), redirect_stderr(err):
        code = stats.main(["stats.py", *args])
    return code, out.getvalue(), err.getvalue()


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


class FileTestCase(unittest.TestCase):
    """Base class giving tests a temporary directory to write number files into."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name

    def write(self, text, name="numbers.txt"):
        path = os.path.join(self.dir, name)
        with open(path, "w") as f:
            f.write(text)
        return path


class NoOptionRegressionTest(FileTestCase):
    """Behaviour without any option must stay exactly as it was at 867f65e."""

    def test_file(self):
        path = self.write("1\n2\n2\n")
        self.assertEqual(run_main([path]), (0, "count 3\nmean 1.66667\n", ""))

    def test_stdin(self):
        self.assertEqual(run_main([], "1.5\n2.5\n"), (0, "count 2\nmean 2\n", ""))

    def test_missing_file(self):
        path = os.path.join(self.dir, "absent.txt")
        self.assertEqual(
            run_main([path]),
            (1, "", f"stats.py: No such file or directory: {path}\n"),
        )

    def test_empty_file_name(self):
        self.assertEqual(run_main([""]), (1, "", "stats.py: No such file or directory: \n"))

    def test_non_number_line(self):
        with self.assertRaises(SystemExit) as caught:
            run_main([], "1\nabc\n")
        self.assertEqual(caught.exception.code, "stats.py: line 2: not a number: 'abc'")

    def test_non_number_line_in_file(self):
        path = self.write("1\n\nx y\n")
        with self.assertRaises(SystemExit) as caught:
            run_main([path])
        self.assertEqual(caught.exception.code, "stats.py: line 3: not a number: 'x y'")

    def test_no_numbers(self):
        self.assertEqual(run_main([], "\n\n"), (1, "", "stats.py: no numbers\n"))

    def test_two_files_is_usage_error(self):
        self.assertEqual(run_main(["a", "b"]), (2, "", "usage: stats.py [FILE]\n"))

    def test_unknown_dash_token_is_a_file(self):
        # Only the four exact flags are options; `--data` is a file name as before.
        old = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(os.chdir, old)
        self.assertEqual(
            run_main(["--data"]),
            (1, "", "stats.py: No such file or directory: --data\n"),
        )
        self.write("4\n", name="--data")
        self.assertEqual(run_main(["--data"]), (0, "count 1\nmean 4\n", ""))

    def test_mean_is_summed_in_input_order(self):
        # The exact result of this sum depends on the order (and on the Python
        # version's sum()), so compare with the original expression.
        numbers = [1e16, 1.0, -1e16, 1.0]
        expected = f"count 4\nmean {sum(numbers) / len(numbers):g}\n"
        self.assertEqual(run_main([], "1e16\n1\n-1e16\n1\n"), (0, expected, ""))


class ParseArgsTest(FileTestCase):
    def test_flags_recognised_in_any_position_and_order(self):
        self.assertEqual(
            stats.parse_args(["--json", "f", "--stdev", "--median", "--minmax", "--json"]),
            ({"--median", "--minmax", "--stdev", "--json"}, ["f"]),
        )

    def test_only_exact_flags_are_options(self):
        self.assertEqual(
            stats.parse_args(["--medians", "-median", "--JSON", "--stdev=1"]),
            (set(), ["--medians", "-median", "--JSON", "--stdev=1"]),
        )

    def test_flags_do_not_count_as_files(self):
        path = self.write("1\n2\n")
        code, _, err = run_main(["--median", path, "--minmax", "--stdev", "--json"])
        self.assertEqual((code, err), (0, ""))
        code, _, err = run_main(["--median", "--json"], "1\n2\n")
        self.assertEqual((code, err), (0, ""))

    def test_flags_with_two_files_is_usage_error(self):
        self.assertEqual(run_main(["--median", "a", "b"]), (2, "", "usage: stats.py [FILE]\n"))

    def test_flags_keep_errors(self):
        self.assertEqual(run_main(["--stdev"], ""), (1, "", "stats.py: no numbers\n"))


class ComputeRenderTest(unittest.TestCase):
    def test_compute_without_options(self):
        pairs = stats.compute([1.0, 2.0, 6.0], set())
        self.assertEqual(pairs, [("count", 3), ("mean", 3.0)])
        self.assertIsInstance(pairs[0][1], int)
        self.assertIsInstance(pairs[1][1], float)

    def test_compute_does_not_modify_numbers(self):
        numbers = [3.0, 1.0, 2.0]
        stats.compute(numbers, set(stats.OPTIONS))
        self.assertEqual(numbers, [3.0, 1.0, 2.0])

    def test_render_plain_formats(self):
        out = io.StringIO()
        with redirect_stdout(out):
            stats.render_plain([("count", 3), ("mean", 5 / 3), ("max", 1e20), ("min", 2.0)])
        self.assertEqual(out.getvalue(), "count 3\nmean 1.66667\nmax 1e+20\nmin 2\n")


class MedianTest(FileTestCase):
    def test_odd_unsorted_input(self):
        self.assertEqual(
            run_main(["--median"], "9\n1\n3\n"),
            (0, "count 3\nmean 4.33333\nmedian 3\n", ""),
        )

    def test_even_unsorted_file(self):
        path = self.write("10\n2\n4\n8\n")
        self.assertEqual(
            run_main(["--median", path]),
            (0, "count 4\nmean 6\nmedian 6\n", ""),
        )

    def test_single_number(self):
        self.assertEqual(
            run_main(["--median"], "-2.5\n"),
            (0, "count 1\nmean -2.5\nmedian -2.5\n", ""),
        )

    def test_even_negative_and_zero(self):
        self.assertEqual(
            run_main(["--median"], "0\n-3\n"),
            (0, "count 2\nmean -1.5\nmedian -1.5\n", ""),
        )

    def test_duplicates_and_repeated_flag_after_file(self):
        path = self.write("4\n2\n2\n2\n")
        self.assertEqual(
            run_main([path, "--median", "--median"]),
            (0, "count 4\nmean 2.5\nmedian 2\n", ""),
        )

    def test_g_format(self):
        self.assertEqual(
            run_main(["--median"], "1.23456789\n"),
            (0, "count 1\nmean 1.23457\nmedian 1.23457\n", ""),
        )


if __name__ == "__main__":
    unittest.main()
