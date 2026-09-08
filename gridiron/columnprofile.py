"""Column profiling: what is actually in this column, counted before it is trusted.

Before a column is summed or joined or charted, the honest
first question is what it actually holds, and a profiler
answers it without judgment: how many cells are filled, how
many empty, how many are numbers versus text versus booleans
versus errors, how many distinct values, and for the numeric
part the min, max, and mean. The value of profiling is that
it counts every kind separately rather than coercing, so a
column that looks numeric but holds three text cells reports
those three rather than silently treating them as zero, which
is how a total comes out low and nobody knows why. Errors are
their own category, never folded into the numeric summary,
because the mean of a column with a #DIV/0! in it is not a
smaller mean, it is undefined, and the profiler says how many
wounds are present rather than pretending they are data. The
distinct count uses the engine's own equality, so the number
5 and the text five are two distinct values, matching how
every other part of the grid refuses to conflate them. An
entirely empty column profiles as empty rather than raising,
because empty is a true and useful answer to what is in this
column, and the numeric summary of no numbers is reported as
absent rather than a min of positive infinity that leaks the
implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.refs import RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value, is_error


@dataclass
class ColumnProfile:
    filled: int
    empty: int
    numbers: int
    texts: int
    booleans: int
    errors: int
    distinct: int
    minimum: float | None
    maximum: float | None
    mean: float | None

    def line(self) -> str:
        numeric = (
            f"min {self.minimum}, max {self.maximum}, "
            f"mean {self.mean:.4g}"
            if self.mean is not None
            else "no numeric summary"
        )
        return (
            f"{self.filled} filled ({self.numbers} number, "
            f"{self.texts} text, {self.booleans} bool, "
            f"{self.errors} error), {self.empty} empty, "
            f"{self.distinct} distinct; {numeric}"
        )


def _hashable(value: Value):
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, float):
        return ("number", value)
    if isinstance(value, str):
        return ("text", value)
    if is_error(value):
        return ("error", value.code)
    return ("blank",)


def profile_column(
    sheet: Sheet, region: RangeRef
) -> ColumnProfile:
    numbers: list[float] = []
    texts = booleans = errors = empty = 0
    seen = set()
    for cell in region.cells():
        value = sheet.value_of(cell)
        if value is None:
            empty += 1
            continue
        seen.add(_hashable(value))
        if is_error(value):
            errors += 1
        elif isinstance(value, bool):
            booleans += 1
        elif isinstance(value, float):
            numbers.append(value)
        elif isinstance(value, str):
            texts += 1
    filled = len(numbers) + texts + booleans + errors
    if numbers:
        minimum = min(numbers)
        maximum = max(numbers)
        mean = sum(numbers) / len(numbers)
    else:
        minimum = maximum = mean = None
    return ColumnProfile(
        filled=filled,
        empty=empty,
        numbers=len(numbers),
        texts=texts,
        booleans=booleans,
        errors=errors,
        distinct=len(seen),
        minimum=minimum,
        maximum=maximum,
        mean=mean,
    )
