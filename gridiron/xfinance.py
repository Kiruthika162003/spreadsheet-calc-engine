"""Dated cash flows: NPV and IRR that know a payment's actual calendar date.

Plain NPV and IRR assume evenly spaced periods, and most real
cash flows are not evenly spaced, so XNPV and XIRR discount by
the actual number of days from the first date on a
three-sixty-five basis. The day-count convention is stated
because it is a real choice, actual over three-sixty-five,
and picking it silently is how two desks value the same
project a little differently and argue about it later. XNPV
requires the dates and amounts to pair, refused by their two
counts otherwise, because a cash flow without its date has no
place on the timeline. XIRR finds the rate where XNPV is
zero, by bisection on the discount curve, and refuses when
the flows never change sign, because a stream that only pays
out or only takes in has no internal rate and inventing one
would be the most expensive number the module prints, the
same refusal the plain IRR makes. MIRR is the modified
internal rate that answers IRR's honest critique of itself:
it discounts the negative flows at a finance rate and
compounds the positive flows at a reinvestment rate, so the
single rate it returns does not assume every interim cash
flow was reinvented at the IRR itself, an assumption that
flatters a project that cannot actually reinvest at that
rate. Each refuses fewer than two flows, because a rate of
return on a single number is not a rate, it is that number.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _years_from_start(dates: list[int]) -> list[float]:
    start = dates[0]
    return [(d - start) / 365.0 for d in dates]


def xnpv(
    rate: float,
    amounts: list[float],
    dates: list[int],
) -> float:
    if len(amounts) != len(dates):
        raise Invalid(
            f"{len(amounts)} amount(s) and {len(dates)} "
            "date(s); a cash flow without its date has no "
            "place on the timeline"
        )
    if len(amounts) < 2:
        raise Invalid(
            "XNPV needs at least two dated flows"
        )
    if dates != sorted(dates):
        raise Invalid(
            "the dates must be non-decreasing; the first is "
            "the valuation date"
        )
    years = _years_from_start(dates)
    return sum(
        amount / (1 + rate) ** t
        for amount, t in zip(amounts, years, strict=True)
    )


def xirr(
    amounts: list[float], dates: list[int]
) -> float:
    if not (
        any(a > 0 for a in amounts)
        and any(a < 0 for a in amounts)
    ):
        raise Invalid(
            "the flows never change sign; a stream that only "
            "pays out or only takes in has no internal rate"
        )
    low, high = -0.9999, 100.0

    def value(rate: float) -> float:
        return xnpv(rate, amounts, dates)

    low_value = value(low)
    high_value = value(high)
    if low_value * high_value > 0:
        raise Invalid(
            "no rate in the searched band zeroes XNPV; the "
            "search refuses a midpoint it never bracketed"
        )
    for _ in range(200):
        mid = (low + high) / 2
        mid_value = value(mid)
        if abs(mid_value) < 1e-7:
            return mid
        if low_value * mid_value < 0:
            high = mid
        else:
            low = mid
            low_value = mid_value
    return (low + high) / 2


def mirr(
    amounts: list[float],
    finance_rate: float,
    reinvest_rate: float,
) -> float:
    if len(amounts) < 2:
        raise Invalid("MIRR needs at least two flows")
    n = len(amounts) - 1
    negatives = 0.0
    positives = 0.0
    for period, amount in enumerate(amounts):
        if amount < 0:
            negatives += amount / (
                1 + finance_rate
            ) ** period
        else:
            positives += amount * (
                1 + reinvest_rate
            ) ** (n - period)
    if negatives == 0 or positives == 0:
        raise Invalid(
            "MIRR needs both an outflow and an inflow; one "
            "sign alone has no modified rate"
        )
    return (-positives / negatives) ** (1.0 / n) - 1.0
