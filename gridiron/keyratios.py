"""Key ratios: the handful of numbers an analyst reads a company by.

Financial statements are dense, and analysts compress them
into a few ratios, each answering one question, and each with
a denominator that can be zero. The discipline here is
uniform: every ratio divides, so every ratio names what it
divides by and refuses a zero denominator rather than
returning infinity, because a debt-to-equity of infinity on a
company with no equity is a real and dangerous condition that
deserves a stated refusal, not a number that silently breaks
the next calculation. The quick ratio is the acid test,
current assets minus inventory over current liabilities,
stricter than the current ratio because inventory is the
asset hardest to turn into cash in a hurry. Debt-to-equity
measures leverage. Return on equity and return on assets
measure how hard the capital works, net income over equity
and over assets. Asset turnover measures efficiency, revenue
per dollar of assets. The gross and net margins live here too
so an analyst reads all the ratios from one place rather than
computing margins in the statement module and leverage here
and wondering which convention each used. Every input is a
statement total the caller already has, so this module does
no accounting itself, it only forms the ratios, which keeps
the one responsibility of turning totals into comparisons
clean and testable.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _ratio(numerator: float, denominator: float, what: str) -> float:
    if denominator == 0:
        raise Invalid(
            f"{what} divides by zero; the condition is real "
            "but the number is not, so it is refused rather "
            "than returned as infinity"
        )
    return numerator / denominator


def current_ratio(
    current_assets: float, current_liabilities: float
) -> float:
    return _ratio(
        current_assets,
        current_liabilities,
        "the current ratio",
    )


def quick_ratio(
    current_assets: float,
    inventory: float,
    current_liabilities: float,
) -> float:
    return _ratio(
        current_assets - inventory,
        current_liabilities,
        "the quick ratio",
    )


def debt_to_equity(
    total_liabilities: float, total_equity: float
) -> float:
    return _ratio(
        total_liabilities, total_equity, "debt-to-equity"
    )


def return_on_equity(
    net_income: float, total_equity: float
) -> float:
    return _ratio(
        net_income, total_equity, "return on equity"
    )


def return_on_assets(
    net_income: float, total_assets: float
) -> float:
    return _ratio(
        net_income, total_assets, "return on assets"
    )


def asset_turnover(
    revenue: float, total_assets: float
) -> float:
    return _ratio(
        revenue, total_assets, "asset turnover"
    )


def gross_margin(
    gross_profit: float, revenue: float
) -> float:
    return _ratio(gross_profit, revenue, "gross margin")


def net_margin(net_income: float, revenue: float) -> float:
    return _ratio(net_income, revenue, "net margin")
