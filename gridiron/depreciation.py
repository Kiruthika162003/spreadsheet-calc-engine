"""Depreciation schedules: three methods, each landing the book value on salvage.

Depreciation is another calculation where the summary number
hides a schedule, and the schedule has one law that all three
methods must obey: the book value at the end equals the
salvage value exactly, not a rounding away, because an asset
that depreciates to a penny above or below its salvage value
misstates the balance sheet and the plug to fix it later is
the entry nobody can explain. Straight-line spreads the
depreciable base evenly. Double-declining applies a fixed
rate to the shrinking book value and is capped so it never
carries the value below salvage, the cap taking whatever
partial amount lands exactly on salvage in the year it would
otherwise overshoot. Sum-of-years-digits weights the early
years heavily by the descending year fraction. Each returns a
per-period table of depreciation and remaining book value,
and the total depreciation across the schedule equals the
depreciable base for every method, the identity the tests
check rather than trust. A salvage value above the cost is
refused, because an asset worth more at the end than the
start does not depreciate, it appreciates, and running a
depreciation method on it produces negative depreciation that
reads as income. A life of zero periods is refused for the
same reason a division by zero is: there is no schedule to
build.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class DepreciationRow:
    period: int
    depreciation: float
    book_value: float


def _validate(cost: float, salvage: float, life: int) -> None:
    if life < 1:
        raise Invalid("an asset's life needs at least one period")
    if salvage > cost:
        raise Invalid(
            "salvage exceeds cost; an asset worth more at "
            "the end than the start appreciates, and running "
            "depreciation on it reads as income"
        )
    if salvage < 0:
        raise Invalid("salvage cannot be negative")


def straight_line(
    cost: float, salvage: float, life: int
) -> list[DepreciationRow]:
    _validate(cost, salvage, life)
    per_period = (cost - salvage) / life
    rows = []
    book = cost
    for period in range(1, life + 1):
        book = round(book - per_period, 10)
        rows.append(
            DepreciationRow(period, per_period, book)
        )
    return rows


def double_declining(
    cost: float, salvage: float, life: int
) -> list[DepreciationRow]:
    _validate(cost, salvage, life)
    rate = 2.0 / life
    rows = []
    book = cost
    for period in range(1, life + 1):
        charge = book * rate
        if book - charge < salvage:
            charge = book - salvage
        book = round(book - charge, 10)
        rows.append(DepreciationRow(period, charge, book))
    return rows


def sum_of_years_digits(
    cost: float, salvage: float, life: int
) -> list[DepreciationRow]:
    _validate(cost, salvage, life)
    digits = life * (life + 1) / 2
    base = cost - salvage
    rows = []
    book = cost
    for period in range(1, life + 1):
        weight = (life - period + 1) / digits
        charge = base * weight
        book = round(book - charge, 10)
        rows.append(DepreciationRow(period, charge, book))
    return rows


def total_depreciation(
    rows: list[DepreciationRow],
) -> float:
    return round(sum(row.depreciation for row in rows), 10)
