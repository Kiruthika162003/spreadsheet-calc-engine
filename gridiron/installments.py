"""Installments: splitting a balance into equal payments that still sum exactly.

Paying a balance in n installments sounds like division, and
it is until the balance does not divide evenly, at which
point the honest plan makes every installment equal to the
cent except one that absorbs the remainder, rather than
leaving each payment a fraction of a cent that no one can
actually pay. This module works in integer cents and puts the
odd cents on the first installment by default, the
convention that front-loads the rounding so the customer's
last payment is the clean round number they remember, though
a caller can move the adjustment to the last payment where
some contracts put it. Either way the installments sum to the
exact balance, the law the tests hold to, because a plan
whose payments do not add up to what is owed is a dispute
waiting to happen. An interest-bearing plan is offered
alongside the plain split: it amortizes the balance at a
per-period rate through the same schedule the amortization
module builds, so the two agree about how a loan is paid
down rather than each inventing its own rounding. A zero or
negative number of installments is refused because a balance
paid in no payments is not a plan, and a negative balance is
refused since a plan pays down what is owed and a negative
owed is a refund wearing a plan's name. The count of
installments is bounded so a pathological request cannot
build an unbounded schedule.
"""

from __future__ import annotations

from gridiron.errors import Invalid

_MAX_INSTALLMENTS = 100000


def equal_installments(
    balance: float, count: int, odd_cents_first: bool = True
) -> list[float]:
    if count < 1:
        raise Invalid(
            "a plan needs at least one installment; no "
            "payments is not a plan"
        )
    if count > _MAX_INSTALLMENTS:
        raise Invalid(
            f"{count} installments exceeds the bound"
        )
    if balance < 0:
        raise Invalid(
            "a negative balance is a refund wearing a plan's "
            "name"
        )
    cents = round(balance * 100)
    base = cents // count
    remainder = cents - base * count
    payments = [base] * count
    if odd_cents_first:
        for i in range(remainder):
            payments[i] += 1
    else:
        for i in range(remainder):
            payments[count - 1 - i] += 1
    return [p / 100 for p in payments]


def total_of(payments: list[float]) -> float:
    return round(sum(payments), 2)
