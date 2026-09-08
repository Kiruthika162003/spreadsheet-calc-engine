"""Late fees: a grace period, then a flat charge and daily interest, honestly capped.

A late payment fee is a small piece of arithmetic with a
disproportionate ability to be unfair, so its rules are made
explicit. There is a grace period, and a payment inside it
owes nothing, no flat fee and no interest, because a charge
one day into a stated grace window is the kind of thing that
ends up in a regulator's inbox. Past the grace, the fee is a
flat charge plus daily interest on the overdue balance, and
the interest accrues only on the days actually late, counted
from the due date, not from the invoice date, because
charging interest for the grace days the borrower was told
were free is charging for a promise. The total fee is capped
at a stated fraction of the balance, because uncapped daily
interest on a small balance left long enough grows to exceed
the balance itself, a usury result many jurisdictions forbid
and none of them intend; the cap is applied to the flat-plus-
interest sum so a caller sees the fee actually charged, not a
theoretical one. Zero days late owes nothing regardless of
grace, the boundary case. A negative balance, a negative
rate, or a negative grace is refused as the data error it is,
since a late fee on a credit balance is charging someone for
money the lender owes them. The days late are computed from
two date serials so the caller passes real dates rather than
a pre-counted number that hides whether the grace was
applied.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class LateFee:
    days_late: int
    chargeable_days: int
    fee: float
    capped: bool


def compute_late_fee(
    balance: float,
    days_late: int,
    flat_fee: float,
    daily_rate: float,
    grace_days: int = 0,
    cap_fraction: float = 0.25,
) -> LateFee:
    if balance < 0:
        raise Invalid(
            "a late fee on a credit balance charges someone "
            "for money the lender owes them"
        )
    if flat_fee < 0 or daily_rate < 0 or grace_days < 0:
        raise Invalid(
            "fees, rates, and grace periods are non-negative"
        )
    if days_late < 0:
        raise Invalid(
            "days late cannot be negative; a payment before "
            "its due date is early, not late"
        )
    if days_late <= grace_days:
        return LateFee(
            days_late=days_late,
            chargeable_days=0,
            fee=0.0,
            capped=False,
        )
    chargeable = days_late - grace_days
    raw = flat_fee + balance * daily_rate * chargeable
    cap = balance * cap_fraction
    capped = raw > cap
    fee = min(raw, cap)
    return LateFee(
        days_late=days_late,
        chargeable_days=chargeable,
        fee=round(fee, 2),
        capped=capped,
    )
