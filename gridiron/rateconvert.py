"""Rate conversion: the nominal rate, the effective rate, and why they differ.

A quoted annual rate is nominal, compounded some number of
times a year, and the effective rate is what it actually
earns once that compounding is counted, so five percent
compounded monthly earns more than five percent compounded
annually and the gap is the whole reason both numbers exist.
EFFECT turns a nominal rate and a compounding frequency into
the effective annual rate; NOMINAL inverts it. The two are
exact inverses, a round trip the tests hold to, because a
pair of conversions that did not return the original rate
would let a spreadsheet quote one number and earn another.
The compounding frequency must be a positive whole number,
refused otherwise, because a rate compounded two-and-a-half
times a year is not a product anyone sells and a zero or
negative frequency divides or roots by nonsense. Continuous
compounding is offered as its own function rather than
folded into EFFECT with an infinite frequency, because the
limit is a different formula, e to the rate minus one, and
pretending a very large frequency approximates it invites
someone to pass a million and wonder why the answer is a hair
off. A nominal rate at or below negative one is refused, since
money that shrinks by more than its whole value in a period
is a modeling error, not a negative interest scenario, the
same floor the discounted cash-flow module draws.
"""

from __future__ import annotations

import math

from gridiron.errors import Invalid


def _validate(rate: float, periods: int) -> None:
    if periods < 1:
        raise Invalid(
            "compounding happens a positive whole number of "
            "times a year"
        )
    if rate <= -1:
        raise Invalid(
            "a rate at or below minus one shrinks money past "
            "its whole value; that is a modeling error"
        )


def effective(nominal: float, periods: int) -> float:
    _validate(nominal, periods)
    return (1 + nominal / periods) ** periods - 1


def nominal(effective_rate: float, periods: int) -> float:
    if periods < 1:
        raise Invalid(
            "compounding happens a positive whole number of "
            "times a year"
        )
    if effective_rate <= -1:
        raise Invalid(
            "an effective rate at or below minus one is a "
            "modeling error"
        )
    return periods * (
        (1 + effective_rate) ** (1 / periods) - 1
    )


def effective_continuous(nominal_rate: float) -> float:
    if nominal_rate <= -1:
        raise Invalid(
            "a rate at or below minus one is a modeling error"
        )
    return math.exp(nominal_rate) - 1


def nominal_continuous(effective_rate: float) -> float:
    if effective_rate <= -1:
        raise Invalid(
            "an effective rate at or below minus one is a "
            "modeling error"
        )
    return math.log(1 + effective_rate)
