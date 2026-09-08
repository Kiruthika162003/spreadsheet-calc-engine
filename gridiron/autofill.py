"""Autofill: the guess about what comes next, made in the open.

Drag-to-fill is the most used inference engine in office
software and the least documented, so this one documents
itself: given the seed cells, it names the pattern it saw
before extending it, and a caller who dislikes the guess can
read the verdict instead of the filled cells. The detection
ladder is ordered from strict to generous. Two or more
numbers advancing by a constant difference fill as that
arithmetic series, a single number fills as repetition, not
as a plus-one series, because the incumbent's habit of
counting up from one seed is the guess users most often
undo. Known cycles fill by rotation from the seed's position,
weekday and month names in short and long forms, wrapping
at the end because that is what calendars do. Text carrying
one trailing number, Item 1, Item 2, advances the number
and keeps the stem, and the stems must agree across seeds or
the fill refuses rather than averaging two ideas. Mixed
seeds that fit no rung of the ladder refuse by name, since a
fill that silently repeats when it did not understand is an
inference engine lying about having inferred.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import pairwise

from gridiron.errors import Invalid
from gridiron.values import Value, render

WEEKDAYS_SHORT = (
    "MON",
    "TUE",
    "WED",
    "THU",
    "FRI",
    "SAT",
    "SUN",
)
WEEKDAYS_LONG = (
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
    "SUNDAY",
)
MONTHS_SHORT = (
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
)
MONTHS_LONG = (
    "JANUARY",
    "FEBRUARY",
    "MARCH",
    "APRIL",
    "MAY",
    "JUNE",
    "JULY",
    "AUGUST",
    "SEPTEMBER",
    "OCTOBER",
    "NOVEMBER",
    "DECEMBER",
)

_CYCLES = (
    ("short weekdays", WEEKDAYS_SHORT),
    ("long weekdays", WEEKDAYS_LONG),
    ("short months", MONTHS_SHORT),
    ("long months", MONTHS_LONG),
)

_STEM_NUMBER = re.compile(r"^(.*?)(\d+)$")


@dataclass(frozen=True)
class FillPlan:
    pattern: str
    values: tuple[Value, ...]

    def verdict(self) -> str:
        preview = ", ".join(
            render(value)
            if isinstance(value, float)
            else str(value)
            for value in self.values[:3]
        )
        more = (
            "..." if len(self.values) > 3 else ""
        )
        return f"{self.pattern}: {preview}{more}"


def _match_case(sample: str, text: str) -> str:
    if sample.isupper():
        return text
    if sample[0].isupper():
        return text.capitalize()
    return text.lower()


def _cycle_fill(
    seeds: list[str], count: int
) -> FillPlan | None:
    upper = [seed.upper() for seed in seeds]
    for label, cycle in _CYCLES:
        if not all(item in cycle for item in upper):
            continue
        positions = [cycle.index(item) for item in upper]
        steps = {
            (b - a) % len(cycle)
            for a, b in pairwise(positions)
        }
        if len(seeds) == 1:
            step = 1
        elif len(steps) == 1 and steps != {0}:
            step = steps.pop()
        else:
            continue
        values = []
        position = positions[-1]
        for _ in range(count):
            position = (position + step) % len(cycle)
            values.append(
                _match_case(seeds[0], cycle[position])
            )
        return FillPlan(
            pattern=f"rotation through {label}",
            values=tuple(values),
        )
    return None


def _numeric_fill(
    seeds: list[float], count: int
) -> FillPlan:
    if len(seeds) == 1:
        return FillPlan(
            pattern="repetition of a lone number",
            values=tuple([seeds[0]] * count),
        )
    differences = {
        round(b - a, 10) for a, b in pairwise(seeds)
    }
    if len(differences) == 1:
        step = differences.pop()
        last = seeds[-1]
        values = tuple(
            last + step * offset
            for offset in range(1, count + 1)
        )
        kind = (
            "constant repetition"
            if step == 0
            else f"arithmetic series, step {render(step)}"
        )
        return FillPlan(pattern=kind, values=values)
    raise Invalid(
        "the numbers advance by no constant difference; "
        "an inference engine that fills anyway is lying "
        "about having inferred"
    )


def _stem_fill(
    seeds: list[str], count: int
) -> FillPlan | None:
    matches = [_STEM_NUMBER.match(seed) for seed in seeds]
    if not all(matches):
        return None
    stems = {match.group(1) for match in matches}
    if len(stems) != 1:
        raise Invalid(
            "the stems disagree; a fill will not average "
            "two ideas"
        )
    stem = stems.pop()
    numbers = [int(match.group(2)) for match in matches]
    if len(numbers) == 1:
        step = 1
    else:
        differences = {
            b - a for a, b in pairwise(numbers)
        }
        if len(differences) != 1:
            raise Invalid(
                "the trailing numbers advance by no "
                "constant difference"
            )
        step = differences.pop()
    last = numbers[-1]
    values = tuple(
        f"{stem}{last + step * offset}"
        for offset in range(1, count + 1)
    )
    return FillPlan(
        pattern=f"numbered stem {stem.strip()!r}",
        values=values,
    )


def plan_fill(seeds: list[Value], count: int) -> FillPlan:
    if not seeds:
        raise Invalid("a fill needs at least one seed")
    if count < 1:
        raise Invalid("a fill needs somewhere to go")
    if all(
        isinstance(seed, float)
        and not isinstance(seed, bool)
        for seed in seeds
    ):
        return _numeric_fill(list(seeds), count)
    if all(
        isinstance(seed, str) and seed.strip()
        for seed in seeds
    ):
        texts = [seed.strip() for seed in seeds]
        cycled = _cycle_fill(texts, count)
        if cycled is not None:
            return cycled
        stemmed = _stem_fill(texts, count)
        if stemmed is not None:
            return stemmed
        if len(set(texts)) == 1:
            return FillPlan(
                pattern="repetition of a lone label",
                values=tuple([texts[0]] * count),
            )
        raise Invalid(
            "no rung of the ladder fits these seeds; "
            "refusing beats silently repeating"
        )
    raise Invalid(
        "the seeds mix kinds; a fill will not average "
        "two ideas"
    )
