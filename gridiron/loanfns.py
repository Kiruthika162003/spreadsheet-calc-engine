"""Loan payment components: how much of each payment is interest, how much principal.

A level loan payment is constant, but its split between
interest and principal shifts every period: early payments
are mostly interest on a large balance, late ones mostly
principal, and the whole point of these functions is to
report that split without building the entire schedule when a
caller wants one period. IPMT is the interest portion of a
given period's payment, PPMT the principal portion, and the
two always sum to the level payment, an identity the tests
hold to, because a split that did not add back to the payment
would be describing a different loan. The sign convention is
the finance module's: a loan is positive cash received now,
so the payments, interest, and principal are negative money
leaving the borrower, and flipping them to look friendly
would make these disagree with PMT about the same loan. The
cumulative forms sum the per-period pieces over an inclusive
range of periods, the calculation an amortization footnote
actually shows, and they refuse a range that runs backward or
steps outside the loan's life rather than summing an empty or
nonsensical span, because a cumulative interest figure over
periods that do not exist is a number with no referent. A
period of zero or beyond the term is refused for the same
reason: there is no payment there to split.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _level_payment(
    rate: float, nper: int, pv: float
) -> float:
    if rate == 0:
        return -pv / nper
    growth = (1 + rate) ** nper
    return -pv * rate * growth / (growth - 1)


def _balance_before(
    rate: float, nper: int, pv: float, period: int
) -> float:
    # Outstanding balance at the start of `period`.
    payment = _level_payment(rate, nper, pv)
    if rate == 0:
        return pv + payment * (period - 1)
    growth = (1 + rate) ** (period - 1)
    return pv * growth + payment * (growth - 1) / rate


def _validate(rate: float, nper: int, period: int) -> None:
    if nper < 1:
        raise Invalid("a loan needs at least one period")
    if not 1 <= period <= nper:
        raise Invalid(
            f"period {period} is outside the loan's "
            f"{nper} period(s); there is no payment there "
            "to split"
        )


def ipmt(
    rate: float, period: int, nper: int, pv: float
) -> float:
    _validate(rate, nper, period)
    balance = _balance_before(rate, nper, pv, period)
    return -balance * rate


def ppmt(
    rate: float, period: int, nper: int, pv: float
) -> float:
    _validate(rate, nper, period)
    payment = _level_payment(rate, nper, pv)
    return payment - ipmt(rate, period, nper, pv)


def cumipmt(
    rate: float,
    nper: int,
    pv: float,
    start: int,
    end: int,
) -> float:
    if start > end:
        raise Invalid(
            "the period range runs backward; a cumulative "
            "figure over a reversed span has no referent"
        )
    return sum(
        ipmt(rate, period, nper, pv)
        for period in range(start, end + 1)
    )


def cumprinc(
    rate: float,
    nper: int,
    pv: float,
    start: int,
    end: int,
) -> float:
    if start > end:
        raise Invalid(
            "the period range runs backward"
        )
    return sum(
        ppmt(rate, period, nper, pv)
        for period in range(start, end + 1)
    )
