"""Cash rounding: snapping a total to the smallest coin, and showing the give-up.

Where the smallest coin is larger than a cent, a cash total
is rounded to the nearest coin, the penny and sometimes the
nickel having been retired, and the honest version reports
the adjustment, the difference between the exact total and
the rounded one, because that difference is money someone
gains or loses on every transaction and a system that hid it
would quietly accumulate a discrepancy the till cannot
explain. Rounding is to the nearest multiple of the
denomination, ties going to the nearest even multiple, the
banker's rule that keeps a long run of half-cent roundings
from drifting the till in one direction, which round-half-up
would do a penny at a time until the drawer is off by
dollars. The rounded amount and the adjustment always sum
back to the exact total, an identity the tests hold to,
because a rounding whose pieces do not reconcile is worse
than no rounding. Electronic and card totals are not rounded,
only cash, so the caller decides when to apply this rather
than the function assuming every total is cash, and the
denomination must be positive, because a zero or negative
smallest coin is not a currency, it is a division by nothing.
Rounding is exact to the cent internally by working in
integer cents, so a denomination of five cents snaps cleanly
rather than accumulating the float error that makes 0.1 plus
0.2 not quite 0.3.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class RoundedCash:
    exact: float
    rounded: float
    adjustment: float


def round_cash(
    amount: float, denomination: float = 0.05
) -> RoundedCash:
    if denomination <= 0:
        raise Invalid(
            "the smallest coin must be positive; a zero "
            "denomination is a division by nothing"
        )
    cents = round(amount * 100)
    step = round(denomination * 100)
    if step == 0:
        raise Invalid(
            "the denomination rounds to less than a cent"
        )
    quotient = cents / step
    lower = int(quotient)
    frac = quotient - lower
    if frac < 0.5:
        multiples = lower
    elif frac > 0.5:
        multiples = lower + 1
    else:
        # Tie: round to the even multiple.
        multiples = lower if lower % 2 == 0 else lower + 1
    rounded_cents = multiples * step
    rounded = rounded_cents / 100
    exact = cents / 100
    return RoundedCash(
        exact=exact,
        rounded=rounded,
        adjustment=round(rounded - exact, 10),
    )
