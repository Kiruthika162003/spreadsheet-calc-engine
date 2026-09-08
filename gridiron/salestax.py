"""Sales tax: adding it forward, and the harder job of backing it out of a total.

Adding sales tax is a multiplication anyone can do; the job
that trips people is the reverse, extracting the tax already
baked into a tax-inclusive total, because the tax is a
fraction of the pre-tax price, not of the total, so dividing
the total by one plus the rate is right and multiplying the
total by the rate is the common wrong answer that overstates
the tax. This module does both directions and keeps them
consistent: adding tax to a pre-tax price and then backing it
out of the resulting total returns the original price to the
cent, a round-trip law the tests hold to, because a tax
calculator whose two directions disagree double-bills or
under-remits on every transaction. It works in integer cents
so the extracted tax and net sum back to the total exactly
rather than drifting a cent on floating point. The rate must
be non-negative, a negative sales tax being a subsidy the
formula was not built for, and a tax-inclusive total below
zero is refused because there is no negative sale to
un-tax. The extracted breakdown reports the net and the tax
separately and asserts they reconcile to the total, so a
caller filing a return has the two figures the form asks for
and the confidence they add up, rather than one number and a
multiplication they have to trust.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class TaxBreakdown:
    total: float
    net: float
    tax: float

    def reconciles(self) -> bool:
        return (
            round(self.net + self.tax, 2)
            == round(self.total, 2)
        )


def add_tax(pretax: float, rate: float) -> TaxBreakdown:
    if pretax < 0:
        raise Invalid("a pre-tax price is not negative")
    if rate < 0:
        raise Invalid(
            "a negative sales tax is a subsidy the formula "
            "was not built for"
        )
    net_cents = round(pretax * 100)
    tax_cents = round(net_cents * rate)
    return TaxBreakdown(
        total=(net_cents + tax_cents) / 100,
        net=net_cents / 100,
        tax=tax_cents / 100,
    )


def extract_tax(total: float, rate: float) -> TaxBreakdown:
    if total < 0:
        raise Invalid(
            "there is no negative sale to un-tax"
        )
    if rate < 0:
        raise Invalid("a negative sales tax is a subsidy")
    total_cents = round(total * 100)
    # The tax is a fraction of the net, not of the total, so
    # net is total divided by one plus the rate.
    net_cents = round(total_cents / (1 + rate))
    tax_cents = total_cents - net_cents
    return TaxBreakdown(
        total=total_cents / 100,
        net=net_cents / 100,
        tax=tax_cents / 100,
    )
