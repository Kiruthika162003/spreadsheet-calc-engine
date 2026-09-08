"""Financial ratios: growth, return, and payback, each refusing its nonsense case.

These are the summary numbers a business plan lives and dies
on, and each has a domain where the arithmetic runs but the
answer is meaningless, which is where the discipline lives.
CAGR, the compound annual growth rate, needs a positive
beginning and ending value and a positive span of years,
because a growth rate from or to a non-positive value is a
root of a negative number, a complex quantity no board deck
should contain, and it is refused rather than returned as a
nan. ROI is a ratio and its denominator is the cost, so a
zero cost is refused as the division it is, because infinite
return on zero investment is a line that has ended a due
diligence early. The payback period walks a stream of cash
flows and reports the period in which the running total
first turns non-negative, interpolating within that period
for the fractional answer, and it reports that the investment
never pays back rather than returning the stream length as if
it had, because a project that never recovers its outlay has
a payback of never, not of its last period. Break-even
divides fixed costs by the contribution margin per unit and
refuses a non-positive margin, since a product that loses
money on every unit never breaks even no matter the volume,
and reporting a negative break-even quantity would invite
someone to plan for it.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def cagr(
    begin: float, end: float, years: float
) -> float:
    if begin <= 0 or end <= 0:
        raise Invalid(
            "CAGR needs positive beginning and ending "
            "values; a rate from or to zero is a complex "
            "root, not a percentage"
        )
    if years <= 0:
        raise Invalid(
            "CAGR needs a positive span of years"
        )
    return (end / begin) ** (1.0 / years) - 1.0


def roi(gain: float, cost: float) -> float:
    if cost == 0:
        raise Invalid(
            "ROI divides by cost; infinite return on zero "
            "investment has ended a diligence early"
        )
    return (gain - cost) / cost


def payback_period(
    cash_flows: list[float],
) -> float | None:
    if not cash_flows:
        raise Invalid("a payback needs cash flows")
    running = 0.0
    previous = 0.0
    for period, flow in enumerate(cash_flows):
        previous = running
        running += flow
        if running >= 0 and period == 0:
            return 0.0
        if running >= 0:
            needed = -previous
            fraction = (
                needed / flow if flow != 0 else 0.0
            )
            return (period - 1) + fraction
    return None


def break_even(
    fixed_cost: float,
    price_per_unit: float,
    variable_cost_per_unit: float,
) -> float:
    margin = price_per_unit - variable_cost_per_unit
    if margin <= 0:
        raise Invalid(
            "the contribution margin is not positive; a "
            "product that loses money on every unit never "
            "breaks even, and a negative break-even invites "
            "planning for it"
        )
    if fixed_cost < 0:
        raise Invalid("fixed cost cannot be negative")
    return fixed_cost / margin
