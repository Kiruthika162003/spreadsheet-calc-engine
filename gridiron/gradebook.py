"""Gradebook: weighted categories, dropped scores, and the letter at the end.

A course grade is a weighted average of category averages,
homework worth one weight and exams another, and the two
places it goes wrong are both about what happens when a
category is incomplete. First, the category weights must sum
to one, or the final grade is scaled by whatever they
actually sum to and a student is quietly graded out of
eighty-seven percent; this module refuses weights that do not
sum to one rather than normalizing them silently, because a
teacher who typed the wrong weight should be told, not
rescued into a different grade. Second, an empty category,
one with no scores yet, cannot contribute an average, and the
honest handling is to renormalize the remaining weights so a
mid-semester grade reflects only what has been graded rather
than treating ungraded work as zeros that crater the average.
Dropping the lowest n scores in a category is supported
because it is a real policy, and it drops before averaging,
refusing to drop more scores than exist rather than leaving a
category empty by policy. The letter grade comes from a
threshold scale applied to the final percentage, and the
scale is a parameter because schools disagree about where the
lines fall, with the boundary rule stated: a score exactly on
a threshold earns the higher letter, because a ninety is an
A-minus, not the top of the B range.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid

DEFAULT_SCALE = (
    (90.0, "A"),
    (80.0, "B"),
    (70.0, "C"),
    (60.0, "D"),
    (0.0, "F"),
)


@dataclass
class Category:
    name: str
    weight: float
    scores: list[float] = field(default_factory=list)
    drop_lowest: int = 0

    def average(self) -> float | None:
        if not self.scores:
            return None
        if self.drop_lowest >= len(self.scores):
            raise Invalid(
                f"{self.name} drops {self.drop_lowest} of "
                f"{len(self.scores)} score(s), leaving the "
                "category empty by policy"
            )
        kept = sorted(self.scores)[self.drop_lowest :]
        return sum(kept) / len(kept)


def course_percentage(
    categories: list[Category],
) -> float:
    total_weight = sum(c.weight for c in categories)
    if abs(total_weight - 1.0) > 1e-9:
        raise Invalid(
            f"the category weights sum to {total_weight}, "
            "not 1; a grade scaled by the wrong total marks "
            "a student out of the wrong denominator"
        )
    active = [
        (c.weight, c.average())
        for c in categories
        if c.average() is not None
    ]
    if not active:
        raise Invalid(
            "no category has any scores yet; there is no "
            "grade to compute"
        )
    live_weight = sum(weight for weight, _ in active)
    return sum(
        (weight / live_weight) * avg
        for weight, avg in active
    )


def letter_grade(
    percentage: float,
    scale: tuple[tuple[float, str], ...] = DEFAULT_SCALE,
) -> str:
    for threshold, letter in scale:
        if percentage >= threshold:
            return letter
    raise Invalid(
        f"{percentage} falls below every threshold in the "
        "scale; the scale needs a floor"
    )
