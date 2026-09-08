"""Pricing: markup versus margin, and why a chain of discounts is not their sum.

Two pricing confusions cost real money, and this module
draws both lines clearly. The first is markup versus margin:
markup is profit over cost, margin is profit over price, and
they are different numbers for the same sale, a fifty percent
markup being only a thirty-three percent margin, so a
merchant who sets a markup thinking it is the margin
under-earns on every unit. The module converts between them
explicitly and never lets one stand in for the other. The
second is the discount chain: successive discounts do not
add, twenty percent then ten percent is not thirty percent
off but twenty-eight, because the second discount applies to
the already-reduced price, and a buyer or seller who summed
them misprices the deal. The module composes a chain
multiplicatively and reports the equivalent single discount,
the honest one-number summary of the whole chain. Margins at
or above one are refused because a hundred percent margin
means the cost was zero and above it means negative cost, a
product that pays you to make it, which is a data error not a
pricing. A discount of a hundred percent or more is refused
for the mirror reason: a full discount is a giveaway the
markup and margin formulas cannot invert, and over a hundred
is paying the customer to take it. Cost and price must be
positive, since a zero or negative one breaks every ratio the
module forms and a free product has no markup to speak of.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def markup_to_margin(markup: float) -> float:
    if markup < 0:
        raise Invalid("a markup is not negative")
    return markup / (1 + markup)


def margin_to_markup(margin: float) -> float:
    if not 0 <= margin < 1:
        raise Invalid(
            f"margin {margin} must sit in [0, 1); a margin "
            "of one means zero cost and above it negative "
            "cost, a product that pays you to make it"
        )
    return margin / (1 - margin)


def price_from_cost(cost: float, markup: float) -> float:
    if cost <= 0:
        raise Invalid(
            "cost must be positive; a free product has no "
            "markup to speak of"
        )
    if markup < 0:
        raise Invalid("a markup is not negative")
    return cost * (1 + markup)


def margin_of(cost: float, price: float) -> float:
    if price <= 0:
        raise Invalid("price must be positive")
    if cost < 0:
        raise Invalid("cost is not negative")
    return (price - cost) / price


def chain_discount(discounts: list[float]) -> float:
    """The single equivalent discount of applying each in turn."""
    remaining = 1.0
    for discount in discounts:
        if not 0 <= discount < 1:
            raise Invalid(
                f"discount {discount} must sit in [0, 1); a "
                "full discount is a giveaway and more is "
                "paying the customer to take it"
            )
        remaining *= 1 - discount
    return 1 - remaining
