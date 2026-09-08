"""Unit pricing: comparing package sizes by what each costs per unit, honestly.

The bigger package is not always the better deal, and the
only way to know is the price per unit, so this module
divides each option's price by its quantity and ranks them,
turning the shelf's deliberately incomparable sizes into one
comparable number. The comparison is only valid when the
quantities share a unit, so the module takes them already in
a common unit and trusts the caller to have converted, but
it refuses a zero or negative quantity because a package of
nothing has an infinite or nonsensical unit price that would
sort to the front as a phantom best deal. Ties in unit price
are broken toward the option listed first so the ranking is
reproducible rather than dependent on input order, and the
best value is reported alongside the full ranking because a
shopper wants both the answer and the runners-up to sanity
check it. The savings of the best over the worst is reported
as a fraction, the honest way to say how much the size
choice matters, and it is undefined and omitted when only one
option is given, because there is no comparison to save
against. A negative price is refused as the data error it is,
since a store does not pay you to take the item, and the unit
prices are kept at full precision rather than rounded for
display, because rounding two close options to the same cent
would hide which actually wins.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Option:
    label: str
    price: float
    quantity: float


@dataclass(frozen=True)
class Ranked:
    label: str
    unit_price: float


def rank(options: list[Option]) -> list[Ranked]:
    if not options:
        raise Invalid("no options to compare")
    scored = []
    for index, option in enumerate(options):
        if option.quantity <= 0:
            raise Invalid(
                f"{option.label!r} has quantity "
                f"{option.quantity}; a package of nothing "
                "has no honest unit price"
            )
        if option.price < 0:
            raise Invalid(
                f"{option.label!r} has a negative price; a "
                "store does not pay you to take the item"
            )
        scored.append(
            (index, option.label, option.price / option.quantity)
        )
    scored.sort(key=lambda t: (t[2], t[0]))
    return [Ranked(label=lbl, unit_price=up) for _, lbl, up in scored]


def best_value(options: list[Option]) -> Ranked:
    return rank(options)[0]


def savings_fraction(options: list[Option]) -> float | None:
    ranked = rank(options)
    if len(ranked) < 2:
        return None
    best = ranked[0].unit_price
    worst = ranked[-1].unit_price
    if worst == 0:
        return 0.0
    return (worst - best) / worst
