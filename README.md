# stats

Summary statistics for numbers, one per line, using only Python's standard library.

    python stats.py [--median] [--minmax] [--stdev] [--json] [FILE]

With no FILE, read standard input. Blank lines are ignored. Count and mean are
always printed; without options, output and errors keep their original form.

| Option | Additional output |
| --- | --- |
| `--median` | Median; for even counts, the mean of the two middle numbers. |
| `--minmax` | Smallest (`min`) and largest (`max`) values. |
| `--stdev` | Sample standard deviation (denominator `n - 1`); one number gives zero. |
| `--json` | One JSON object containing count, mean and every requested statistic. |

Options can appear before or after FILE, in any order; repeats are harmless.
Output order is always `count`, `mean`, `median`, `min`, `max`, `stdev`, omitting
unrequested statistics. Plain numbers use Python's `g` formatting. JSON uses the
same rounded numeric values, with an integer count and floats for other values.

For a file `numbers.txt` containing `1`, `2`, and `3` on separate lines:

```console
$ python stats.py --stdev --minmax --median numbers.txt
count 3
mean 2
median 2
min 1
max 3
stdev 1
$ python stats.py --json --median --minmax --stdev numbers.txt
{"count": 3, "mean": 2.0, "median": 2.0, "min": 1.0, "max": 3.0, "stdev": 1.0}
```

Only the four exact flags are options. Other tokens, including misspelled options,
are filenames. Use a path such as `./--median` to read a file named like a flag.
Missing files, empty input and non-number lines exit with status 1; more than one
FILE exits with status 2. Errors go to stderr and produce no statistics on stdout.

Nonfinite values (`nan`, `inf`) remain accepted. A multi-value sample containing
a nonfinite value prints `stdev nan`; a singleton prints `stdev 0`. JSON follows `json.dumps`
defaults and may contain `NaN` or `Infinity`, which strict JSON readers reject.
Min/max with NaN can depend on input order. Very large finite samples can overflow
`statistics.stdev` on older Python versions such as 3.9.

Run the tests with `python -m unittest`. They cover individual options, all option
subsets and orders, FILE placement, JSON values and no-option compatibility.
The CLI flow in `stats.py` is `parse_args` → `read_numbers` → `compute` → the plain
or JSON renderer. Computation preserves input order for the mean; it does not
modify the input list. There is no build or deployment step: run the script
directly. To roll back a change, restore its previous Git revision.
