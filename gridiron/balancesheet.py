"""Balance sheets: assets, liabilities, equity, and the equation that must hold.

A balance sheet is three stacks of line items with one law
older than spreadsheets: assets equal liabilities plus
equity. A sheet where they do not is not a balance sheet, it
is a mistake, so this builder computes the three totals and
reports whether they balance rather than assuming they do,
and the difference when they do not, because the size of the
imbalance is the first clue to which entry is wrong. The
totals are derived from the line items, never entered, for
the same reason a P&L derives its subtotals: a hand-typed
total that disagrees with its components is the error the
statement exists to surface. Current and long-term are
tracked as subgroups within assets and liabilities because
the current ratio, current assets over current liabilities,
is the liquidity number every reader checks next, and it is
reported as absent when current liabilities are zero rather
than dividing by them, because infinite liquidity is a
degenerate case better shown than faked. Working capital,
current assets minus current liabilities, is reported
alongside because it is the same comparison in absolute
rather than ratio form and the two answer the question
differently for a reader who prefers dollars to multiples. A
line item may be negative, a contra-asset like accumulated
depreciation is legitimately negative, so negatives are kept
rather than refused, and the balancing check catches the
sign error a blanket refusal would miss anyway.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BalanceSheet:
    current_assets: list[tuple[str, float]] = field(
        default_factory=list
    )
    longterm_assets: list[tuple[str, float]] = field(
        default_factory=list
    )
    current_liabilities: list[tuple[str, float]] = field(
        default_factory=list
    )
    longterm_liabilities: list[tuple[str, float]] = field(
        default_factory=list
    )
    equity: list[tuple[str, float]] = field(
        default_factory=list
    )

    def total_current_assets(self) -> float:
        return sum(v for _, v in self.current_assets)

    def total_assets(self) -> float:
        return self.total_current_assets() + sum(
            v for _, v in self.longterm_assets
        )

    def total_current_liabilities(self) -> float:
        return sum(v for _, v in self.current_liabilities)

    def total_liabilities(self) -> float:
        return self.total_current_liabilities() + sum(
            v for _, v in self.longterm_liabilities
        )

    def total_equity(self) -> float:
        return sum(v for _, v in self.equity)

    def imbalance(self) -> float:
        return round(
            self.total_assets()
            - self.total_liabilities()
            - self.total_equity(),
            10,
        )

    def balances(self) -> bool:
        return self.imbalance() == 0

    def current_ratio(self) -> float | None:
        current_liabilities = (
            self.total_current_liabilities()
        )
        if current_liabilities == 0:
            return None
        return (
            self.total_current_assets()
            / current_liabilities
        )

    def working_capital(self) -> float:
        return (
            self.total_current_assets()
            - self.total_current_liabilities()
        )
