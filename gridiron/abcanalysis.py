"""ABC analysis: sorting inventory into the vital few and the trivial many.

ABC analysis is Pareto applied to inventory: rank items by
annual dollar value, and the top slice that accounts for most
of the value is class A, worth tight control, the middle is
B, and the long cheap tail is C, worth little attention. The
classification is by cumulative value share against two
cutoffs, conventionally eighty and ninety-five percent, and
the boundary rule is the one that quietly reclassifies items
if left implicit: an item belongs to the band its cumulative
share lands in, so an item at or below the A cutoff is A and
the first item whose cumulative crosses that cutoff has
entered the B band and is B. An item landing exactly on a
cutoff belongs to the lower, tighter-control class, because a
value sitting precisely on the eighty-percent line is still
within the vital few, not past them. Items are
ranked largest first and ties keep input order so the
classification is reproducible. The cutoffs must rise and sit
inside zero and one, refused otherwise, because an A cutoff
above the B cutoff would put the vital few below the trivial
many and invert the whole point. A zero total value is
refused, because shares of zero are undefined and every item
would classify by a division that does not exist. The output
carries each item's value, its share, its cumulative share,
and its class, because a bare class letter without the shares
behind it is a verdict the reader cannot check.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class ABCItem:
    label: str
    value: float
    share: float
    cumulative: float
    abc_class: str


def classify(
    items: list[tuple[str, float]],
    a_cutoff: float = 0.80,
    b_cutoff: float = 0.95,
) -> list[ABCItem]:
    if not items:
        raise Invalid("no items to classify")
    if not 0 < a_cutoff < b_cutoff < 1:
        raise Invalid(
            "cutoffs must rise inside (0, 1); an A cutoff "
            "above B would rank the vital few below the "
            "trivial many"
        )
    for label, value in items:
        if value < 0:
            raise Invalid(
                f"{label!r} has a negative value; ABC "
                "analysis ranks contributions to a total"
            )
    total = sum(value for _, value in items)
    if total == 0:
        raise Invalid(
            "the total value is zero; shares are undefined "
            "and every item would classify by a division "
            "that does not exist"
        )
    ordered = sorted(
        enumerate(items),
        key=lambda pair: (-pair[1][1], pair[0]),
    )
    result = []
    running = 0.0
    for _, (label, value) in ordered:
        share = value / total
        running += share
        if running <= a_cutoff + 1e-12:
            abc = "A"
        elif running <= b_cutoff + 1e-12:
            abc = "B"
        else:
            abc = "C"
        result.append(
            ABCItem(
                label=label,
                value=value,
                share=share,
                cumulative=running,
                abc_class=abc,
            )
        )
    return result


def class_totals(
    items: list[ABCItem],
) -> dict[str, int]:
    counts = {"A": 0, "B": 0, "C": 0}
    for item in items:
        counts[item.abc_class] += 1
    return counts
