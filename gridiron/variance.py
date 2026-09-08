"""Budget variance: actual against plan, and the favorable sign that flips by kind.

A variance report compares actual to budget, and the trap
that makes most of them subtly wrong is the sign: a cost that
comes in over budget is bad, but a revenue that comes in over
budget is good, so the same arithmetic difference is
unfavorable for one line and favorable for the other. A
report that labeled every over-budget figure the same way
would tell a manager their record sales quarter was a
problem. This module takes the line's kind, revenue or cost,
and classifies the variance accordingly: for revenue,
actual above budget is favorable; for cost, actual below
budget is favorable. The raw variance is always actual minus
budget so the numbers still add up across a mixed statement,
and only the favorable label depends on the kind, keeping the
arithmetic honest while the interpretation follows the line.
The percent variance divides by the budget and is reported as
absent when the budget is zero, because a percentage over a
zero baseline is undefined and a zero-budget line that spent
anything is infinitely over, a fact better shown as no-percent
than as a number. A variance of exactly zero is neither
favorable nor unfavorable but on-budget, its own third
category, because forcing it into one side or the other
overstates how many lines actually missed.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid

REVENUE = "revenue"
COST = "cost"


@dataclass(frozen=True)
class Variance:
    label: str
    budget: float
    actual: float
    amount: float
    percent: float | None
    verdict: str


def _classify(kind: str, amount: float) -> str:
    if amount == 0:
        return "on-budget"
    if kind == REVENUE:
        return "favorable" if amount > 0 else "unfavorable"
    return "favorable" if amount < 0 else "unfavorable"


def analyze_line(
    label: str,
    budget: float,
    actual: float,
    kind: str,
) -> Variance:
    if kind not in (REVENUE, COST):
        raise Invalid(
            f"unknown line kind {kind!r}; a variance is "
            "favorable or not only relative to whether the "
            "line is revenue or cost"
        )
    amount = actual - budget
    percent = None if budget == 0 else amount / budget
    return Variance(
        label=label,
        budget=budget,
        actual=actual,
        amount=amount,
        percent=percent,
        verdict=_classify(kind, amount),
    )


def analyze(
    lines: list[tuple[str, float, float, str]],
) -> list[Variance]:
    return [
        analyze_line(label, budget, actual, kind)
        for label, budget, actual, kind in lines
    ]


def net_variance(variances: list[Variance]) -> float:
    return round(sum(v.amount for v in variances), 10)
