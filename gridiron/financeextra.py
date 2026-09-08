"""More finance: the time-value quintet, closed where it can be, bisected where it can't.

The five time-value quantities, present value, future value,
payment, rate, and number of periods, are one equation with
five unknowns; PMT already lives in the base finance module,
so this family supplies the other four and solves each
holding the rest fixed. Three of them, FV, PV, and NPER,
have closed forms and get them, with the rate-of-zero case
handled explicitly because the general formula divides by
the rate and simple interest is not a limit worth computing
wrong.
NPER's guard taught the cycle's lesson: the first draft
rejected a negative numerator or denominator outright, but
the logarithm needs only their ratio positive, and a funding
plan with a negative payment produces exactly two negatives
whose ratio is a healthy 1.6, so the guard now tests the
ratio it actually takes the log of. A second measurement
sharpened it further: a plan whose payments run the wrong
way produces a mathematically real but negative term, and a
negative number of periods is nonsense wearing a decimal
point, so the term is refused when it comes out at or below
zero rather than printed as a fact about time running
backward. RATE has no closed form
and is bisected the way IRR is,
because the polynomial in the periodic rate has no algebraic
root, and the bisection refuses to converge rather than
returning the midpoint of an interval it never trusted. The
sign convention is the finance module's and is not
renegotiated here: money out is negative, so a loan taken is
positive present value and its payments are negative, and FV
of a savings plan you fund is negative because the bank owes
it back to you. Depreciation joins the family because it is
the other calculation every asset schedule needs: SLN is
straight-line and DDB is double-declining, and DDB is capped
so it never depreciates an asset below its salvage value,
the error that turns a balance sheet negative on paper.
"""

from __future__ import annotations

from math import log

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)


def _numbers(args, lookup, functions, names, count, label):
    if len(args) != count:
        return ErrorValue(
            code="#VALUE!",
            note=f"{label} takes {count} argument(s)",
        )
    gathered = []
    for arg in args:
        value = to_number(
            evaluate(arg, lookup, functions, names)
        )
        if is_error(value):
            return value
        gathered.append(value)
    return gathered


def _fv(args, lookup, functions, names) -> Value:
    parsed = _numbers(
        args, lookup, functions, names, 4, "FV"
    )
    if is_error(parsed):
        return parsed
    rate, nper, pmt, pv = parsed
    if rate == 0:
        return -(pv + pmt * nper)
    growth = (1 + rate) ** nper
    return -(pv * growth + pmt * (growth - 1) / rate)


def _pv(args, lookup, functions, names) -> Value:
    parsed = _numbers(
        args, lookup, functions, names, 4, "PV"
    )
    if is_error(parsed):
        return parsed
    rate, nper, pmt, fv = parsed
    if rate == 0:
        return -(fv + pmt * nper)
    growth = (1 + rate) ** nper
    return -(fv + pmt * (growth - 1) / rate) / growth


def _nper(args, lookup, functions, names) -> Value:
    parsed = _numbers(
        args, lookup, functions, names, 4, "NPER"
    )
    if is_error(parsed):
        return parsed
    rate, pmt, pv, fv = parsed
    if rate == 0:
        if pmt == 0:
            return ErrorValue(
                code="#NUM!",
                note=(
                    "with no rate and no payment the term "
                    "never ends"
                ),
            )
        return -(pv + fv) / pmt
    numerator = pmt - fv * rate
    denominator = pmt + pv * rate
    non_retiring = ErrorValue(
        code="#NUM!",
        note=(
            "these cash flows never retire the balance; "
            "the term does not converge"
        ),
    )
    if denominator == 0 or numerator / denominator <= 0:
        return non_retiring
    term = log(numerator / denominator) / log(1 + rate)
    if term <= 0:
        return non_retiring
    return term


def _rate(args, lookup, functions, names) -> Value:
    parsed = _numbers(
        args, lookup, functions, names, 3, "RATE"
    )
    if is_error(parsed):
        return parsed
    nper, pmt, pv = parsed
    if nper <= 0:
        return ErrorValue(
            code="#NUM!",
            note="RATE needs a positive number of periods",
        )

    def balance(rate: float) -> float:
        if rate == 0:
            return pv + pmt * nper
        growth = (1 + rate) ** nper
        return pv * growth + pmt * (growth - 1) / rate

    low, high = -0.999999, 1.0
    low_value = balance(low)
    high_value = balance(high)
    if low_value * high_value > 0:
        return ErrorValue(
            code="#NUM!",
            note=(
                "no rate in the searched band balances these "
                "flows; RATE refuses the midpoint of an "
                "interval it never trusted"
            ),
        )
    for _ in range(200):
        mid = (low + high) / 2
        mid_value = balance(mid)
        if abs(mid_value) < 1e-9:
            return mid
        if low_value * mid_value < 0:
            high = mid
        else:
            low = mid
            low_value = mid_value
    return (low + high) / 2


def _sln(args, lookup, functions, names) -> Value:
    parsed = _numbers(
        args, lookup, functions, names, 3, "SLN"
    )
    if is_error(parsed):
        return parsed
    cost, salvage, life = parsed
    if life <= 0:
        return ErrorValue(
            code="#NUM!",
            note="an asset's life must be positive",
        )
    return (cost - salvage) / life


def _ddb(args, lookup, functions, names) -> Value:
    parsed = _numbers(
        args, lookup, functions, names, 4, "DDB"
    )
    if is_error(parsed):
        return parsed
    cost, salvage, life, period = parsed
    if life <= 0 or period < 1 or period > life:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"period {period} is outside an asset life "
                f"of {life}"
            ),
        )
    rate = 2.0 / life
    book = cost
    depreciation = 0.0
    for _ in range(int(period)):
        depreciation = book * rate
        if book - depreciation < salvage:
            depreciation = max(book - salvage, 0.0)
        book -= depreciation
    return depreciation


FINANCE_EXTRA_FUNCTIONS = {
    "FV": _fv,
    "PV": _pv,
    "NPER": _nper,
    "RATE": _rate,
    "SLN": _sln,
    "DDB": _ddb,
}
