# gridiron

A spreadsheet calculation engine, built the way a spreadsheet is
actually used: formulas parsed to trees, recalculated incrementally over
a dependency graph, with circular references quarantined or solved on
purpose rather than crashing the grid. The name of the package is
`gridiron`; the discipline of the package is that every number it
returns can be explained, and every number it refuses to return says
why.

## What it is

The core is small and strict. A lexer and a Pratt parser turn `=A1*2`
into a tree, carrying positions so every syntax error names where it
went wrong, and honoring Excel's precedence including the case everyone
argues about (`-2^2` is 4). An evaluator folds the tree against injected
lookups so a formula can be computed against the live sheet, a what-if
overlay, or a test fixture, and errors flow as values (`#DIV/0!`,
`#VALUE!`, `#REF!`, `#NAME?`, `#CYCLE!`, `#NUM!`, `#N/A`) rather than
raising, first error winning, text refusing to become a number in
silence. A sparse sheet stores each cell's verbatim formula text beside
its parsed tree and its computed value. An incremental engine marks the
exact cells an edit dirties, recomputes their cone in dependency order,
and reports how many formulas slept, because the half of incremental
recalculation everyone forgets to prove is that nothing else was
touched. Cross-sheet references extend the graph across a workbook, and
a book engine settles the cross-sheet formulas in rounds after each
local cone, stamping a workbook loop `#CYCLE!` at the cap rather than
spinning.

Around that core sits a large function library, reachable through one
door, and a wide field of spreadsheet operations: copy and paste that
rewrite references on the tree rather than the text, row and column
insert and delete that bake visible `#REF!` wounds, an iterative solver
that reports convergence or divergence rather than dressing noise as a
result, goal seek and a golden-section optimizer, undo built from what
the setters returned, structured tables whose names resolve against the
live region, pivot tables that weigh records rather than bucket
averages, filters and slicers and outlines, snapshots and scenarios and
a what-if data table, dynamic arrays that spill all-or-nothing, an error
doctor that walks a wound back to its birthplace, and an R1C1 dialect in
which copying is the identity. Beyond the grid proper the library
reaches into statistics, finance, dates, matrices, text, and a broad
band of everyday quantitative work, each function built around the one
edge case its naive version fumbles and each refusing the input that has
no honest answer.

## The measured voice

The docstrings are essays, and they are honest about the build. Where a
first guess was refuted by measurement, the refutation stays recorded
beside the measured truth: the tick ladder that snapped a chart's axis
to three marks until it learned to round at the midpoints; the follower
count that inflated because a tree-rewrite rebuilt every node whether or
not a reference moved; the k-means seeds that starved in the gap between
two clusters until they were placed on the data's own quantiles; the
NPER guard that rejected two negatives whose ratio was a healthy 1.6.
The tests assert the number that was measured, not the one that was
imagined.

## Verifying it

- `python -m pytest tests/` runs the suite: 1,725 tests across 180 test
  modules.
- `python -c "from gridiron.cli import main; main(['summary'])"` runs the
  20 proofs, each an executable claim about a load-bearing property, and
  reports how many hold.
- `python -c "from gridiron.cli import main; main(['check'])"` exits
  nonzero if any proof is broken.
- The `examples/` directory holds 10 runnable end-to-end transcripts,
  each pinned line by line in the test suite.

The engine exposes 167 worksheet functions through
`gridiron.library.full_table`, and the whole codebase is a little over
thirty thousand lines of real logic, comments and blank lines aside.

Written by Kiruthika Subramani in collaboration with Claude, Anthropic's AI assistant.
