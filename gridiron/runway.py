"""Runway: how long the cash lasts, and the honest answer when it lasts forever.

A company's runway is how many months its cash balance
survives at the current net burn, the gap between what it
spends and what it earns, and the calculation has one edge
that decides whether the answer is a number or a word. When
net burn is zero or negative, the company earns at least as
much as it spends and the runway is not a large number, it is
infinite, and this module says so with a distinct
never-runs-out result rather than dividing by zero or
returning a misleadingly huge month count that a reader would
mistake for a deadline. When burn is positive, the runway is
the balance over the monthly net burn, and the module reports
both the raw months and the whole months of safety, the floor,
because a runway of 5.8 months means five months are certain
and the sixth is a gamble on timing, and rounding it up to
six is the optimism that ends a company a month early. The
burn is computed from spend minus revenue so a caller passes
the two real figures rather than a pre-netted number that
hides whether revenue was counted, and a negative balance is
refused because a company already out of cash has no runway
to project, only a hole to explain. The projection is a
straight-line model and says so: it assumes spend and revenue
hold steady, which they never quite do, so the number is a
planning estimate and not a promise, the caveat every runway
slide should carry and rarely does.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Runway:
    net_burn: float
    months: float | None
    whole_months: int | None

    def runs_out(self) -> bool:
        return self.months is not None

    def describe(self) -> str:
        if self.months is None:
            return (
                "cash-flow positive; the runway does not "
                "run out"
            )
        return (
            f"{self.months:.1f} months of runway, "
            f"{self.whole_months} certain"
        )


def compute_runway(
    balance: float,
    monthly_spend: float,
    monthly_revenue: float,
) -> Runway:
    if balance < 0:
        raise Invalid(
            "the balance is already negative; a company out "
            "of cash has a hole to explain, not a runway to "
            "project"
        )
    if monthly_spend < 0 or monthly_revenue < 0:
        raise Invalid(
            "spend and revenue are non-negative amounts; a "
            "negative one is a sign error"
        )
    net_burn = monthly_spend - monthly_revenue
    if net_burn <= 0:
        return Runway(
            net_burn=net_burn,
            months=None,
            whole_months=None,
        )
    months = balance / net_burn
    return Runway(
        net_burn=net_burn,
        months=months,
        whole_months=int(months),
    )
