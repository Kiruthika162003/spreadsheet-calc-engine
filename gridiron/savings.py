"""Savings goals: growing a balance with contributions, and solving for the shortfall.

A savings plan has a starting balance, a periodic
contribution, a rate, and a number of periods, and the two
questions people ask are where does this end up and how much
must I put in to reach a target. Projecting forward is the
future value of the opening balance compounded plus the
future value of the contribution stream, and the module
builds a period-by-period table so a saver sees the balance
climb rather than trusting one closed-form number, with the
final balance read off the table so the two cannot disagree.
Solving for the required contribution inverts that formula
directly at a nonzero rate and falls back to plain division
at a zero rate, because the annuity formula divides by the
rate and simple saving is not a limit worth computing wrong.
The one refusal that matters is an impossible goal: if the
opening balance already compounds past the target with no
contribution at all, the required contribution is zero, not a
negative number that would read as a suggestion to withdraw,
so the solver floors it at zero and says the goal is already
met. A target below the compounded opening balance is that
already-met case; a target reachable only with contributions
gets the positive figure. Contributions are treated as
end-of-period, the convention that pairs with the finance
module's future-value sign, stated so a beginning-of-period
saver knows to expect a slightly higher balance than this
reports.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class SavingsRow:
    period: int
    contribution: float
    interest: float
    balance: float


def project(
    opening: float,
    contribution: float,
    rate: float,
    periods: int,
) -> list[SavingsRow]:
    if periods < 1:
        raise Invalid("a plan needs at least one period")
    rows = []
    balance = opening
    for period in range(1, periods + 1):
        interest = balance * rate
        balance = balance + interest + contribution
        rows.append(
            SavingsRow(
                period=period,
                contribution=contribution,
                interest=interest,
                balance=round(balance, 10),
            )
        )
    return rows


def final_balance(
    opening: float,
    contribution: float,
    rate: float,
    periods: int,
) -> float:
    return project(
        opening, contribution, rate, periods
    )[-1].balance


def required_contribution(
    opening: float,
    target: float,
    rate: float,
    periods: int,
) -> float:
    if periods < 1:
        raise Invalid("a plan needs at least one period")
    if rate == 0:
        grown = opening
        needed = (target - grown) / periods
    else:
        growth = (1 + rate) ** periods
        grown = opening * growth
        annuity_factor = (growth - 1) / rate
        needed = (target - grown) / annuity_factor
    if needed <= 0:
        return 0.0
    return needed
