"""Finance functions: sign conventions stated, IRR found honestly or not at all.

Financial functions have killed more spreadsheet audits than
any other family, and the killer is always the sign
convention: money out is negative, money in is positive, and
PMT returns a negative number for a loan payment because the
payment leaves your pocket. This engine states the
convention in every docstring and keeps it, because flipping
signs to look friendly makes NPV and PMT disagree about the
same cash flow. NPV discounts from period one like the
incumbent, meaning the initial outlay belongs outside the
call, added at face value, the trap every finance course
warns about and every clone must preserve or break every
imported model. IRR bisects the NPV sign change and refuses
when the cash flows never change sign, with the reason: a
project that only pays out or only takes in has no internal
rate, and inventing one would be the most expensive number
the engine ever printed.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)

IRR_BISECTIONS = 200


def _number_arg(args, index, lookup, functions, names):
    return to_number(
        evaluate(args[index], lookup, functions, names)
    )


def _flows(
    arg, lookup
) -> list[float] | ErrorValue:
    if not isinstance(arg, Range):
        return ErrorValue(
            code="#VALUE!",
            note="cash flows arrive as a range",
        )
    flows: list[float] = []
    for cell in arg.ref.cells():
        value = lookup(cell)
        if is_error(value):
            return value
        if isinstance(value, float) and not isinstance(
            value, bool
        ):
            flows.append(value)
    return flows


def _pmt(args, lookup, functions, names) -> Value:
    if len(args) != 3:
        return ErrorValue(
            code="#VALUE!",
            note="PMT takes rate, periods, present value",
        )
    rate = _number_arg(args, 0, lookup, functions, names)
    if is_error(rate):
        return rate
    periods = _number_arg(args, 1, lookup, functions, names)
    if is_error(periods):
        return periods
    present = _number_arg(args, 2, lookup, functions, names)
    if is_error(present):
        return present
    if periods <= 0:
        return ErrorValue(
            code="#NUM!", note="periods must be positive"
        )
    if rate == 0.0:
        return -present / periods
    factor = (1 + rate) ** periods
    return -present * rate * factor / (factor - 1)


def _npv(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "NPV takes a rate and a flow range; the "
                "initial outlay belongs outside the call, at "
                "face value, the trap every course warns about"
            ),
        )
    rate = _number_arg(args, 0, lookup, functions, names)
    if is_error(rate):
        return rate
    flows = _flows(args[1], lookup)
    if is_error(flows):
        return flows
    if rate <= -1.0:
        return ErrorValue(
            code="#NUM!",
            note="a rate at or below minus one hundred percent",
        )
    total = 0.0
    for period, flow in enumerate(flows, start=1):
        total += flow / (1 + rate) ** period
    return total


def _npv_at(rate: float, flows: list[float]) -> float:
    return sum(
        flow / (1 + rate) ** period
        for period, flow in enumerate(flows)
    )


def _irr(args, lookup, _functions, _names) -> Value:
    if len(args) != 1:
        return ErrorValue(
            code="#VALUE!", note="IRR takes a flow range"
        )
    flows = _flows(args[0], lookup)
    if is_error(flows):
        return flows
    if not any(f > 0 for f in flows) or not any(
        f < 0 for f in flows
    ):
        return ErrorValue(
            code="#NUM!",
            note=(
                "the cash flows never change sign; a project "
                "that only pays out or only takes in has no "
                "internal rate, and inventing one would be "
                "the most expensive number this engine ever "
                "printed"
            ),
        )
    low, high = -0.99, 10.0
    low_npv = _npv_at(low, flows)
    high_npv = _npv_at(high, flows)
    if low_npv * high_npv > 0:
        return ErrorValue(
            code="#NUM!",
            note=(
                "no sign change between minus 99 percent and "
                "1000 percent; the rate lives outside any "
                "market this engine will vouch for"
            ),
        )
    for _ in range(IRR_BISECTIONS):
        middle = (low + high) / 2
        middle_npv = _npv_at(middle, flows)
        if abs(middle_npv) < 1e-9:
            return middle
        if (middle_npv < 0) == (low_npv < 0):
            low, low_npv = middle, middle_npv
        else:
            high = middle
    return (low + high) / 2


FINANCE_FUNCTIONS = {
    "PMT": _pmt,
    "NPV": _npv,
    "IRR": _irr,
}
