"""Amortization: a loan paid down period by period, and the balance that lands on zero.

An amortization schedule is where a loan's abstract terms
become a table someone signs, so the arithmetic must close:
after the last payment the balance is exactly zero, not a
penny of rounding drift left to become a phantom final
invoice. This builder computes the level payment from the
standard annuity formula, then walks the periods splitting
each payment into interest on the outstanding balance and
principal that reduces it, and the closing discipline is
explicit: every intermediate figure is rounded to the cent
as a real statement would show it, and the final period's
principal is whatever remains rather than the formula's
theoretical figure, so the accumulated rounding lands in the
last payment where a borrower expects the odd cent, and the
balance reaches zero exactly. A zero interest rate is handled
as its own case, equal principal each period, rather than
dividing by the rate, because the annuity formula's zero-rate
limit is a division no computer should attempt. The totals
are checked against the schedule rather than recomputed
independently: total principal equals the original balance
and total interest equals total payments minus principal, and
those identities are the schedule proving itself rather than
a claim beside it.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Period:
    number: int
    payment: float
    interest: float
    principal: float
    balance: float


@dataclass
class Schedule:
    periods: list[Period]

    def total_paid(self) -> float:
        return round(
            sum(p.payment for p in self.periods), 2
        )

    def total_interest(self) -> float:
        return round(
            sum(p.interest for p in self.periods), 2
        )

    def total_principal(self) -> float:
        return round(
            sum(p.principal for p in self.periods), 2
        )

    def final_balance(self) -> float:
        return self.periods[-1].balance


def _level_payment(
    principal: float, rate: float, periods: int
) -> float:
    if rate == 0:
        return principal / periods
    growth = (1 + rate) ** periods
    return principal * rate * growth / (growth - 1)


def amortize(
    principal: float, rate: float, periods: int
) -> Schedule:
    if principal <= 0:
        raise Invalid(
            "a loan needs a positive principal"
        )
    if periods < 1:
        raise Invalid(
            "a loan needs at least one period"
        )
    if rate < 0:
        raise Invalid(
            "a negative rate is not a loan; it is a gift "
            "with extra steps"
        )
    payment = round(
        _level_payment(principal, rate, periods), 2
    )
    balance = principal
    rows: list[Period] = []
    for number in range(1, periods + 1):
        interest = round(balance * rate, 2)
        if number == periods:
            principal_part = balance
            this_payment = round(
                principal_part + interest, 2
            )
        else:
            principal_part = round(payment - interest, 2)
            this_payment = payment
        balance = round(balance - principal_part, 2)
        rows.append(
            Period(
                number=number,
                payment=this_payment,
                interest=interest,
                principal=principal_part,
                balance=balance,
            )
        )
    return Schedule(periods=rows)
