"""Aging: sorting balances by how overdue they are, and reconciling to the total.

An aging report buckets outstanding balances by how many
days past due they are, current then thirty, sixty, ninety,
and beyond, and its cardinal discipline is that the buckets
reconcile: every balance lands in exactly one bucket and the
bucket totals sum to the grand total, because an aging report
that does not tie to the ledger it summarizes is the first
thing an auditor catches and the last thing a controller
wants to explain. The bucket boundaries are half-open and
stated: current is zero to thirty days, the thirty bucket is
thirty up to sixty, and so on, so a balance exactly at thirty
days lands in the thirty bucket rather than being counted in
both or neither. A balance not yet due, negative days, is its
own bucket rather than folded into current, because a credit
or a prepayment is not an overdue receivable and mixing them
understates what is actually owed now. A negative balance is
kept and reported rather than dropped, because a credit memo
is real money that must still tie to the total, and silently
dropping it makes the report disagree with the ledger by
exactly the amount most worth noticing. The boundaries are a
parameter with a sensible default, because not every business
ages on the same calendar, and a report that hard-coded
thirty-day buckets would lie for the one that bills weekly.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid

DEFAULT_BOUNDARIES = (0, 30, 60, 90)


@dataclass
class AgingReport:
    buckets: dict[str, float]
    total: float

    def reconciles(self) -> bool:
        return abs(
            sum(self.buckets.values()) - self.total
        ) < 1e-9

    def line(self) -> str:
        parts = [
            f"{name}: {amount:g}"
            for name, amount in self.buckets.items()
        ]
        return "; ".join(parts) + f"; total {self.total:g}"


def _bucket_names(
    boundaries: tuple[int, ...],
) -> list[str]:
    names = ["not due"]
    for index, edge in enumerate(boundaries):
        if index + 1 < len(boundaries):
            names.append(
                f"{edge}-{boundaries[index + 1]}"
            )
        else:
            names.append(f"{edge}+")
    return names


def age_balances(
    items: list[tuple[float, int]],
    boundaries: tuple[int, ...] = DEFAULT_BOUNDARIES,
) -> AgingReport:
    if not boundaries or list(boundaries) != sorted(
        boundaries
    ):
        raise Invalid(
            "the aging boundaries must rise; an unsorted "
            "ladder buckets the wrong balances"
        )
    if boundaries[0] != 0:
        raise Invalid(
            "the first boundary is zero days; everything "
            "current is due from day zero"
        )
    names = _bucket_names(boundaries)
    buckets = dict.fromkeys(names, 0.0)
    total = 0.0
    for amount, days in items:
        total += amount
        if days < 0:
            buckets["not due"] += amount
            continue
        placed = False
        for index in range(len(boundaries)):
            low = boundaries[index]
            high = (
                boundaries[index + 1]
                if index + 1 < len(boundaries)
                else None
            )
            if high is None or low <= days < high:
                buckets[names[index + 1]] += amount
                placed = True
                break
        if not placed:
            buckets[names[-1]] += amount
    return AgingReport(buckets=buckets, total=total)
