"""Pareto analysis: the vital few, sorted, and the cumulative line that finds them.

The eighty-twenty rule is a claim a spreadsheet can check
rather than assume: sort the contributors by size, walk the
cumulative share, and see how few account for most of the
total. This module builds that table, each item carrying its
own share of the grand total and the running cumulative
share through it, sorted largest first because that is the
order the rule is read in. The cutoff is a stated threshold,
default eighty percent, and the vital few are the items up to
and including the one that first crosses it, because stopping
just before the crossing would exclude the item that pushed
past the line and misstate where the bulk actually sits. Two
honest refusals guard the arithmetic. A total of zero has no
shares to compute, division by it is undefined, and it is
refused rather than returning shares of infinity. And a
negative contribution is refused, because Pareto analysis
assumes contributions that add toward a total, and a negative
value makes the cumulative share non-monotonic, so the line
that is supposed to climb to a hundred percent would dip and
the vital-few cutoff would land somewhere meaningless. Ties
in size keep their input order so the same data always ranks
the same way, and the shares sum to one within floating-point
dust, the table proving itself against the total it came
from.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class ParetoItem:
    label: str
    value: float
    share: float
    cumulative: float
    vital: bool


def analyze(
    items: list[tuple[str, float]],
    threshold: float = 0.8,
) -> list[ParetoItem]:
    if not items:
        raise Invalid("no items to analyze")
    for label, value in items:
        if value < 0:
            raise Invalid(
                f"{label!r} contributes {value}; Pareto "
                "analysis assumes contributions toward a "
                "total, and a negative makes the cumulative "
                "line dip below itself"
            )
    total = sum(value for _, value in items)
    if total == 0:
        raise Invalid(
            "the total is zero; there are no shares to "
            "compute and division by it is undefined"
        )
    ordered = sorted(
        enumerate(items),
        key=lambda pair: (-pair[1][1], pair[0]),
    )
    result: list[ParetoItem] = []
    running = 0.0
    crossed = False
    for _, (label, value) in ordered:
        share = value / total
        running += share
        vital = not crossed
        if running >= threshold:
            crossed = True
        result.append(
            ParetoItem(
                label=label,
                value=value,
                share=share,
                cumulative=running,
                vital=vital,
            )
        )
    return result


def vital_few(
    items: list[tuple[str, float]],
    threshold: float = 0.8,
) -> list[str]:
    return [
        item.label
        for item in analyze(items, threshold)
        if item.vital
    ]
