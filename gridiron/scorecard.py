"""Scorecards: ranking options on weighted criteria, normalized so scales cannot cheat.

A decision matrix scores several options against several
weighted criteria and ranks them, and the failure that makes
most of them meaningless is un-normalized scales: a criterion
measured in thousands silently dominates one measured in
tens, not because it matters more but because its numbers are
bigger, so the weights become a lie. This module normalizes
every criterion to a zero-to-one scale before weighting,
mapping each column's worst value to zero and its best to
one, so a weight of thirty percent means thirty percent of
the decision regardless of the units the criterion was
measured in. The direction matters and is stated per
criterion: for a benefit criterion higher is better and the
maximum maps to one, for a cost criterion lower is better and
the minimum maps to one, because normalizing a cost the same
way as a benefit would rank the most expensive option best.
A criterion where every option scores the same has no
spread to normalize, and rather than dividing by a zero range
it contributes its weight equally to all, since a criterion
that does not distinguish the options should not tip the
ranking. The weights must sum to one, refused otherwise for
the same reason a gradebook refuses it: a total score scaled
by the wrong denominator ranks by a number no one can
interpret. Ties in the final score keep input order so the
ranking is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Criterion:
    name: str
    weight: float
    benefit: bool = True


@dataclass(frozen=True)
class Scored:
    option: str
    score: float


def score(
    options: list[str],
    criteria: list[Criterion],
    values: dict[str, list[float]],
) -> list[Scored]:
    if not options or not criteria:
        raise Invalid("a scorecard needs options and criteria")
    total_weight = sum(c.weight for c in criteria)
    if abs(total_weight - 1.0) > 1e-9:
        raise Invalid(
            f"the weights sum to {total_weight}, not one; a "
            "score scaled by the wrong denominator ranks by "
            "a number no one can interpret"
        )
    for option in options:
        if len(values.get(option, [])) != len(criteria):
            raise Invalid(
                f"option {option!r} needs one value per "
                "criterion"
            )
    totals = dict.fromkeys(options, 0.0)
    for index, criterion in enumerate(criteria):
        column = [values[o][index] for o in options]
        low, high = min(column), max(column)
        span = high - low
        for option in options:
            raw = values[option][index]
            if span == 0:
                normalized = 1.0
            elif criterion.benefit:
                normalized = (raw - low) / span
            else:
                normalized = (high - raw) / span
            totals[option] += criterion.weight * normalized
    return sorted(
        (
            Scored(option=o, score=totals[o])
            for o in options
        ),
        key=lambda s: (-s.score, options.index(s.option)),
    )
