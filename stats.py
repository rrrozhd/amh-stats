"""Summary statistics for numbers, one per line, read from a file or standard input."""
import sys


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


def main(argv):
    if len(argv) > 2:
        print("usage: stats.py [FILE]", file=sys.stderr)
        return 2
    if len(argv) == 2:
        try:
            with open(argv[1]) as f:
                numbers = read_numbers(f)
        except OSError as e:
            print(f"stats.py: {e.strerror}: {argv[1]}", file=sys.stderr)
            return 1
    else:
        numbers = read_numbers(sys.stdin)
    if not numbers:
        print("stats.py: no numbers", file=sys.stderr)
        return 1
    print(f"count {len(numbers)}")
    print(f"mean {sum(numbers) / len(numbers):g}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
