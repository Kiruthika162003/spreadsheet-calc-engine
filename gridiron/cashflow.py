"""Discounted cash flow: the schedule that shows its work, period by period.

An NPV is a single number that hides its derivation, and the
first question anyone senior asks is show me the schedule, so
this module builds the table the number came from: each
period's raw flow, its discount factor at the given rate, the
discounted flow, and the running cumulative discounted total.
The summary metrics are read off that table rather than
recomputed independently, so the NPV is exactly the last
cumulative figure and cannot disagree with the rows above it,
which is the reconciliation a spreadsheet audit checks first.
Discounted payback, the period at which the cumulative
discounted flow first turns non-negative, is reported with
interpolation within the period for the fractional answer,
and it reports never rather than the schedule length when the
project does not recover in discounted terms, because a
payback of never is not a payback at the end. The discount
factor convention is stated: period zero is undiscounted,
present value is now, and period one is discounted once, the
end-of-period convention most models assume, chosen out loud
because the alternative, discounting period zero, shifts
every figure and the two models argue about a rounding that
is actually a convention. A negative rate is refused, since a
discount rate below negative one implies money worth less
than nothing next year, a modeling error rather than a
scenario.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class CashFlowRow:
    period: int
    flow: float
    factor: float
    discounted: float
    cumulative: float


@dataclass
class CashFlowSchedule:
    rows: list[CashFlowRow]

    def npv(self) -> float:
        return self.rows[-1].cumulative

    def discounted_payback(self) -> float | None:
        previous = 0.0
        for row in self.rows:
            if row.cumulative >= 0:
                if row.period == 0:
                    return 0.0
                needed = -previous
                step = row.discounted
                fraction = (
                    needed / step if step != 0 else 0.0
                )
                return (row.period - 1) + fraction
            previous = row.cumulative
        return None

    def render(self) -> str:
        lines = [
            "period  flow      discounted  cumulative"
        ]
        for row in self.rows:
            lines.append(
                f"{row.period:<7} {row.flow:<9g} "
                f"{row.discounted:<11.2f} "
                f"{row.cumulative:.2f}"
            )
        lines.append(f"NPV = {self.npv():.2f}")
        return "\n".join(lines)


def build_schedule(
    flows: list[float], rate: float
) -> CashFlowSchedule:
    if not flows:
        raise Invalid("a schedule needs cash flows")
    if rate <= -1:
        raise Invalid(
            "a discount rate at or below minus one implies "
            "money worth less than nothing next year; that "
            "is a modeling error, not a scenario"
        )
    rows: list[CashFlowRow] = []
    cumulative = 0.0
    for period, flow in enumerate(flows):
        factor = 1.0 / (1 + rate) ** period
        discounted = flow * factor
        cumulative += discounted
        rows.append(
            CashFlowRow(
                period=period,
                flow=flow,
                factor=factor,
                discounted=discounted,
                cumulative=cumulative,
            )
        )
    return CashFlowSchedule(rows=rows)
