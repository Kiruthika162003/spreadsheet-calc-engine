"""Progressive brackets: each slice taxed at its own rate, and the marginal-vs-effective trap.

Progressive taxation is the arithmetic everyone gets wrong at
a dinner party: income is sliced at the bracket boundaries
and each slice is taxed at its own rate, so a raise that
pushes the last dollar into a higher bracket taxes only that
dollar higher, never the whole income. The module computes
tax by walking the slices, and it exposes both rates the
conversation confuses, the marginal rate, which is the
bracket the last dollar fell in, and the effective rate,
which is total tax over total income, because reporting only
one of them is how the dinner-party mistake gets made. The
brackets are validated as a rising sequence of thresholds
before any income is taxed, because a bracket table that is
out of order taxes a middle slice at the wrong rate and the
error is invisible in the total until someone in that slice
checks. The first bracket starts at zero implicitly, income
below the first threshold is taxed at the first rate, and an
income of zero owes zero at a zero effective rate rather than
dividing by zero to report the effective rate, because the
tax on nothing is nothing and its rate is a question with a
defined, boring answer. Rates outside zero to one are refused
as the data-entry slip they are, since a hundred-and-ten
percent bracket is a typo, not a policy.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Bracket:
    threshold: float
    rate: float


@dataclass
class TaxResult:
    total_tax: float
    marginal_rate: float
    effective_rate: float


def _validate(brackets: list[Bracket]) -> None:
    if not brackets:
        raise Invalid("a tax table needs at least one bracket")
    if brackets[0].threshold != 0:
        raise Invalid(
            "the first bracket must start at zero income; "
            "everything below the first threshold is taxed "
            "somewhere"
        )
    previous = -1.0
    for bracket in brackets:
        if bracket.threshold <= previous:
            raise Invalid(
                f"threshold {bracket.threshold} does not "
                "rise above the previous; an out-of-order "
                "table taxes a middle slice at the wrong rate"
            )
        if not 0.0 <= bracket.rate <= 1.0:
            raise Invalid(
                f"rate {bracket.rate} is outside 0 to 1; a "
                "hundred-and-ten percent bracket is a typo, "
                "not a policy"
            )
        previous = bracket.threshold


def compute_tax(
    income: float, brackets: list[Bracket]
) -> TaxResult:
    _validate(brackets)
    if income < 0:
        raise Invalid("income cannot be negative")
    total = 0.0
    marginal = brackets[0].rate
    for index, bracket in enumerate(brackets):
        if income <= bracket.threshold:
            break
        upper = (
            brackets[index + 1].threshold
            if index + 1 < len(brackets)
            else income
        )
        slice_top = min(income, upper)
        taxable = slice_top - bracket.threshold
        if taxable > 0:
            total += taxable * bracket.rate
            marginal = bracket.rate
    effective = 0.0 if income == 0 else total / income
    return TaxResult(
        total_tax=round(total, 2),
        marginal_rate=marginal,
        effective_rate=effective,
    )
