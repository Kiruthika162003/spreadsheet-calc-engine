"""Bond math: price from yield in closed form, yield from price by search.

A bond is a stream of coupon payments plus a return of face
value at maturity, and its price is the present value of that
stream at a given yield, which this module computes directly.
The inverse, the yield that produces an observed price, has
no closed form, so it is found by bisection on the
monotonic price-yield curve, the same honest search the
solver and RATE use, and it refuses to converge rather than
returning the midpoint of an interval it never trusted. The
sign discipline is the finance module's: price is positive
money paid now for the bond, coupons and face are positive
money received later, and the yield is the periodic rate that
equates them. Two domain facts are enforced. A bond with zero
periods has already matured and has no price to compute, and
a negative coupon or face is refused as the data-entry slip
it is, since a bond that pays negative coupons is a fee
schedule wearing a bond's name. Macaulay duration, the
present-value-weighted average time to the cash flows, is the
number that answers how much the price moves when the yield
does, and it is computed from the same discounting as the
price so the two cannot disagree about the stream they
describe.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def price(
    face: float,
    coupon_rate: float,
    periods: int,
    yield_rate: float,
) -> float:
    if periods < 1:
        raise Invalid(
            "a bond with no periods has already matured"
        )
    if face < 0 or coupon_rate < 0:
        raise Invalid(
            "a negative face or coupon is a fee schedule "
            "wearing a bond's name"
        )
    coupon = face * coupon_rate
    total = 0.0
    for period in range(1, periods + 1):
        cash = coupon + (face if period == periods else 0.0)
        total += cash / (1 + yield_rate) ** period
    return total


def yield_to_maturity(
    face: float,
    coupon_rate: float,
    periods: int,
    market_price: float,
) -> float:
    if market_price <= 0:
        raise Invalid(
            "a non-positive price has no yield to find"
        )
    low, high = -0.9999, 10.0

    def priced(rate: float) -> float:
        return price(face, coupon_rate, periods, rate)

    if (priced(low) - market_price) * (
        priced(high) - market_price
    ) > 0:
        raise Invalid(
            "no yield in the searched band prices this "
            "bond; the search refuses a midpoint it never "
            "bracketed"
        )
    for _ in range(200):
        mid = (low + high) / 2
        value = priced(mid) - market_price
        if abs(value) < 1e-8:
            return mid
        # Price falls as yield rises, so a value above zero
        # means the yield is too low.
        if value > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def macaulay_duration(
    face: float,
    coupon_rate: float,
    periods: int,
    yield_rate: float,
) -> float:
    if periods < 1:
        raise Invalid(
            "a bond with no periods has no duration"
        )
    coupon = face * coupon_rate
    weighted = 0.0
    present = 0.0
    for period in range(1, periods + 1):
        cash = coupon + (face if period == periods else 0.0)
        pv = cash / (1 + yield_rate) ** period
        weighted += period * pv
        present += pv
    if present == 0:
        raise Invalid(
            "the discounted stream is worthless; its "
            "duration is undefined"
        )
    return weighted / present
