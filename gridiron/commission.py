"""Commission: tiered rates on sales, marginal like tax, refusing the cliff.

Sales commission is usually tiered, a low rate on the first
band of sales and higher rates above thresholds, and the
same trap that catches progressive tax catches this: the
rate applies to the sales within each band, not to the whole
figure once a threshold is crossed, so a salesperson who
just clears a tier is paid the higher rate only on the dollar
that cleared it, never retroactively on everything below.
This module computes commission marginally for that reason,
and it exposes both the total commission and the marginal
rate the last dollar earned, because a rep planning the last
push of a quarter needs to know what the next sale pays, not
just what the quarter paid. The tiers are validated as
rising thresholds starting at zero, refused otherwise,
because tiers out of order pay a middle band at the wrong
rate and the error hides in the total until someone in that
band checks their statement. A rate outside zero to one is
refused as the data-entry slip it is, a commission over a
hundred percent paying more than the sale brought in. The
module deliberately implements the marginal scheme rather
than a cliff scheme where crossing a threshold reprices every
dollar, because the cliff creates the perverse incentive to
hold a sale back to next quarter to land in a higher tier,
and a commission plan that rewards not selling is a bug in
the business, not a feature this tool will compute.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Tier:
    threshold: float
    rate: float


@dataclass(frozen=True)
class CommissionResult:
    commission: float
    marginal_rate: float


def _validate(tiers: list[Tier]) -> None:
    if not tiers:
        raise Invalid("a commission plan needs tiers")
    if tiers[0].threshold != 0:
        raise Invalid(
            "the first tier starts at zero sales; every "
            "dollar is commissioned from the first"
        )
    previous = -1.0
    for tier in tiers:
        if tier.threshold <= previous:
            raise Invalid(
                f"tier threshold {tier.threshold} does not "
                "rise; an out-of-order plan pays a middle "
                "band at the wrong rate"
            )
        if not 0.0 <= tier.rate <= 1.0:
            raise Invalid(
                f"rate {tier.rate} is outside 0 to 1; a "
                "commission over the whole sale is a typo"
            )
        previous = tier.threshold


def compute_commission(
    sales: float, tiers: list[Tier]
) -> CommissionResult:
    _validate(tiers)
    if sales < 0:
        raise Invalid("sales cannot be negative")
    total = 0.0
    marginal = tiers[0].rate
    for index, tier in enumerate(tiers):
        if sales <= tier.threshold:
            break
        upper = (
            tiers[index + 1].threshold
            if index + 1 < len(tiers)
            else sales
        )
        band_top = min(sales, upper)
        in_band = band_top - tier.threshold
        if in_band > 0:
            total += in_band * tier.rate
            marginal = tier.rate
    return CommissionResult(
        commission=round(total, 10),
        marginal_rate=marginal,
    )
