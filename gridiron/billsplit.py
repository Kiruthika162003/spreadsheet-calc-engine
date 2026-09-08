"""Bill splitting: tax, tip, and the leftover cent that has to go somewhere.

Splitting a restaurant bill is the everyday version of the
allocation problem, and it has the same non-negotiable: the
shares must sum to the exact total charged, tax and tip
included, or someone quietly covers the difference. This
module computes the total from the subtotal, a tax rate, and
a tip rate, then splits it across diners either evenly or by
each diner's own order, and it works in integer cents so the
shares add up to the penny rather than drifting on floating
point. The tip is taken on the pre-tax subtotal by default,
the convention most people use and the one worth stating
because tipping on the post-tax total quietly tips on the
government's cut too, and the choice is a flag rather than a
silent default. The leftover cents from division go to the
diners by largest remainder, the same fair rule the
allocation module uses, so the person who rounds down one
cent is the one who was closest to rounding up anyway rather
than always the first name on the list. Splitting by order
refuses a diner whose order is missing, because a bill split
by order needs everyone's order and guessing a missing one
is how a table underpays. A negative subtotal, tax, or tip is
refused as the data-entry error it is, since a bill does not
charge a negative amount and a negative tip is a subtraction
wearing a gratuity's name.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.allocate import allocate
from gridiron.errors import Invalid


@dataclass(frozen=True)
class Split:
    total_cents: int
    shares_cents: list[int]

    def total(self) -> float:
        return self.total_cents / 100

    def shares(self) -> list[float]:
        return [c / 100 for c in self.shares_cents]

    def reconciles(self) -> bool:
        return sum(self.shares_cents) == self.total_cents


def _total_cents(
    subtotal: float,
    tax_rate: float,
    tip_rate: float,
    tip_on_pretax: bool,
) -> int:
    if subtotal < 0 or tax_rate < 0 or tip_rate < 0:
        raise Invalid(
            "a bill charges no negative amount; a negative "
            "tip is a subtraction wearing a gratuity's name"
        )
    tax = subtotal * tax_rate
    tip_base = subtotal if tip_on_pretax else subtotal + tax
    tip = tip_base * tip_rate
    return round((subtotal + tax + tip) * 100)


def split_evenly(
    subtotal: float,
    diners: int,
    tax_rate: float = 0.0,
    tip_rate: float = 0.0,
    tip_on_pretax: bool = True,
) -> Split:
    if diners < 1:
        raise Invalid("a bill needs at least one diner")
    total = _total_cents(
        subtotal, tax_rate, tip_rate, tip_on_pretax
    )
    shares = allocate(total, [1.0] * diners)
    return Split(total_cents=total, shares_cents=shares)


def split_by_order(
    orders: list[float],
    tax_rate: float = 0.0,
    tip_rate: float = 0.0,
    tip_on_pretax: bool = True,
) -> Split:
    if not orders:
        raise Invalid("no orders to split")
    if any(o < 0 for o in orders):
        raise Invalid(
            "a diner cannot order a negative amount; a "
            "missing order is not a zero one"
        )
    subtotal = sum(orders)
    total = _total_cents(
        subtotal, tax_rate, tip_rate, tip_on_pretax
    )
    shares = allocate(total, orders)
    return Split(total_cents=total, shares_cents=shares)
