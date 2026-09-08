"""Payroll: gross to net, in the order the deductions actually apply.

Turning a gross salary into take-home pay is a sequence of
subtractions, and the order is not arbitrary, so getting it
wrong quietly overstates or understates the tax. Pre-tax
deductions, retirement contributions and the like, come out
first and reduce the income that tax is computed on, which is
the whole reason they are called pre-tax and the benefit
someone forfeits if the calculator taxes the full gross.
Tax is then computed on that reduced base through the
progressive bracket engine already written, so the two
modules agree about how brackets work rather than each having
its own idea. Post-tax deductions come out last, after tax,
because they are paid from money already taxed and applying
them before tax would give an unearned deduction. The result
reports every stage, gross, pre-tax total, taxable base, tax,
post-tax total, and net, because a paystub that showed only
gross and net would leave the employee unable to check the
middle, and the middle is exactly where a payroll error
hides. Net is never allowed to go negative: deductions that
would take more than remains are refused with the shortfall
named, because a paycheck that owes the employer money is a
data-entry error, not a payslip, and issuing it is worse than
stopping to ask.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.taxbrackets import Bracket, compute_tax


@dataclass(frozen=True)
class Paystub:
    gross: float
    pretax: float
    taxable: float
    tax: float
    posttax: float
    net: float

    def reconciles(self) -> bool:
        rebuilt = (
            self.gross
            - self.pretax
            - self.tax
            - self.posttax
        )
        return abs(rebuilt - self.net) < 1e-9


def run_payroll(
    gross: float,
    pretax_deductions: list[float],
    brackets: list[Bracket],
    posttax_deductions: list[float],
) -> Paystub:
    if gross < 0:
        raise Invalid("gross pay cannot be negative")
    pretax = sum(pretax_deductions)
    if any(d < 0 for d in pretax_deductions):
        raise Invalid("a deduction cannot be negative")
    if any(d < 0 for d in posttax_deductions):
        raise Invalid("a deduction cannot be negative")
    if pretax > gross:
        raise Invalid(
            f"pre-tax deductions of {pretax} exceed gross "
            f"pay of {gross}; a paycheck cannot owe the "
            "employer money"
        )
    taxable = gross - pretax
    tax = compute_tax(taxable, brackets).total_tax
    posttax = sum(posttax_deductions)
    net = taxable - tax - posttax
    if net < 0:
        raise Invalid(
            f"deductions and tax exceed pay by {-net:g}; a "
            "negative paycheck is a data-entry error, not a "
            "payslip"
        )
    return Paystub(
        gross=gross,
        pretax=pretax,
        taxable=taxable,
        tax=tax,
        posttax=posttax,
        net=net,
    )
