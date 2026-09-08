"""Income statements: revenue down to net, with the subtotals that must tie.

A profit-and-loss statement is a stack of signed line items
grouped into sections, and the discipline that keeps it
honest is that the subtotals are derived, never entered:
gross profit is revenue minus cost of goods sold, operating
income is gross profit minus operating expenses, net income
is operating income minus everything below the line, and each
is computed from the items above it rather than typed in,
because a hand-entered subtotal that disagrees with its
components is the error that makes a whole statement suspect.
The sign convention is stated: revenue is entered positive
and costs positive, and the statement subtracts the cost
sections rather than expecting the user to enter negatives,
because a P&L full of negative numbers is how a data-entry
slip flips a cost into income unnoticed. Margins are ratios
against revenue, gross margin and net margin, and they are
reported as absent when revenue is zero rather than dividing
by it, because a margin on no revenue is undefined and a
zero-revenue company with costs has an infinitely negative
margin better shown as no-margin than as a number. The
builder returns every subtotal and margin so a reader checks
the arithmetic rather than trusting the bottom line, and the
line items keep their order within each section because the
order a statement is read in is part of what it communicates.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IncomeStatement:
    revenue: list[tuple[str, float]] = field(
        default_factory=list
    )
    cogs: list[tuple[str, float]] = field(
        default_factory=list
    )
    operating: list[tuple[str, float]] = field(
        default_factory=list
    )
    other: list[tuple[str, float]] = field(
        default_factory=list
    )

    def total_revenue(self) -> float:
        return sum(v for _, v in self.revenue)

    def total_cogs(self) -> float:
        return sum(v for _, v in self.cogs)

    def gross_profit(self) -> float:
        return self.total_revenue() - self.total_cogs()

    def total_operating(self) -> float:
        return sum(v for _, v in self.operating)

    def operating_income(self) -> float:
        return self.gross_profit() - self.total_operating()

    def total_other(self) -> float:
        return sum(v for _, v in self.other)

    def net_income(self) -> float:
        return self.operating_income() - self.total_other()

    def gross_margin(self) -> float | None:
        revenue = self.total_revenue()
        if revenue == 0:
            return None
        return self.gross_profit() / revenue

    def net_margin(self) -> float | None:
        revenue = self.total_revenue()
        if revenue == 0:
            return None
        return self.net_income() / revenue

    def render(self) -> str:
        lines = ["Revenue"]
        for label, value in self.revenue:
            lines.append(f"  {label}: {value:g}")
        lines.append(f"Gross profit: {self.gross_profit():g}")
        lines.append(
            f"Operating income: {self.operating_income():g}"
        )
        lines.append(f"Net income: {self.net_income():g}")
        margin = self.net_margin()
        if margin is not None:
            lines.append(f"Net margin: {margin:.1%}")
        return "\n".join(lines)
