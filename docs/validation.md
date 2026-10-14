# Validation — 2026-10-12

Python 3.14.7, macOS. `python -m unittest discover -s tests -v`: **11 passed**.
Tests cover hard-rule vetoes despite high scores, soft failures, mutated fact
strings, footnotes, regex, bounds, hash rules, configuration errors, HTML escaping
and deterministic output.

Built a wheel and installed it in a fresh virtual environment. From a directory
outside the checkout, the installed `rubric-gate` command returned exit 0 for the
passing synthetic example and exit 1 for the blocked example. The browser
screenshot shows the actual generated report for both examples.

The CI matrix targets Python 3.12/3.13 and has not yet run on GitHub. Rule
satisfaction is not a measure of truth, reasoning or style quality. The footnote
checker is deliberately basic; see the rule reference for limits.
