"""Summary statistics for numbers, one per line, read from a file or standard input."""
import json
import math
import statistics
import sys

# The only tokens treated as options. Any other argument, whatever it starts
# with, is the FILE operand, exactly as before the options existed.
OPTIONS = ("--median", "--minmax", "--stdev", "--json")


def read_numbers(stream):
    numbers = []
    for lineno, line in enumerate(stream, 1):
        text = line.strip()
        if not text:
            continue
        try:
            numbers.append(float(text))
        except ValueError:
            raise SystemExit(f"stats.py: line {lineno}: not a number: {text!r}")
    return numbers


def parse_args(args):
    """Split arguments into (options, files); order and repeats of options do not matter."""
    options = set()
    files = []
    for arg in args:
        if arg in OPTIONS:
            options.add(arg)
        else:
            files.append(arg)
    return options, files


def compute(numbers, options):
    """Return the requested statistics as (key, value) pairs.

    The order is fixed here and never depends on the order of the options:
    count, mean, median, min, max, stdev. count is an int, every other value
    a float. Do not sort or otherwise modify `numbers` in place: the mean is
    summed in input order.
    """
    pairs = [
        ("count", len(numbers)),
        ("mean", sum(numbers) / len(numbers)),
    ]
    if "--median" in options:
        pairs.append(("median", statistics.median(numbers)))
    if "--minmax" in options:
        pairs.append(("min", min(numbers)))
        pairs.append(("max", max(numbers)))
    if "--stdev" in options:
        if len(numbers) == 1:
            stdev = 0.0
        elif not all(math.isfinite(value) for value in numbers):
            stdev = math.nan
        else:
            stdev = statistics.stdev(numbers)
        pairs.append(("stdev", stdev))
    return pairs


def render_plain(pairs):
    """Print one `key value` line per pair: count as an integer, the rest in `g` format."""
    for key, value in pairs:
        if key == "count":
            print(f"{key} {value}")
        else:
            print(f"{key} {value:g}")


def render_json(pairs):
    """Print one object with the same numeric values as the plain output."""
    values = {key: value if key == "count" else float(format(value, "g"))
              for key, value in pairs}
    print(json.dumps(values))


def main(argv):
    options, files = parse_args(argv[1:])
    if len(files) > 1:
        print("usage: stats.py [FILE]", file=sys.stderr)
        return 2
    filename = files[0] if files else None
    if filename is not None:
        try:
            with open(filename) as f:
                numbers = read_numbers(f)
        except OSError as e:
            print(f"stats.py: {e.strerror}: {filename}", file=sys.stderr)
            return 1
    else:
        numbers = read_numbers(sys.stdin)
    if not numbers:
        print("stats.py: no numbers", file=sys.stderr)
        return 1
    pairs = compute(numbers, options)
    if "--json" in options:
        render_json(pairs)
    else:
        render_plain(pairs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
