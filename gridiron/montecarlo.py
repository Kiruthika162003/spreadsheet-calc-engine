"""Monte Carlo: many random trials of a model, made reproducible by a seed.

A Monte Carlo estimate runs a model thousands of times over
randomly sampled inputs and reports the distribution of the
outcomes, which is how a spreadsheet answers what-if when the
inputs are ranges rather than points. The requirement the
word random hides is the same one the sampling module already
insisted on: reproducibility. A simulation whose answer
changes every run is one nobody can cite, so every trial here
draws from the seeded generator, and the same seed with the
same model gives the same estimate, down to the last decimal,
so a result in a report can be regenerated and checked. The
inputs are uniform ranges, each a low and a high, and the
model is a function of the sampled values; the module runs
the trials, collects the outputs, and reports the mean and a
percentile band rather than a single number, because the
point of a simulation is the spread and a lone mean throws
away the very uncertainty the simulation was run to measure.
A trial that raises is not swallowed: if the model errors on
some sampled input, the whole estimate stops and surfaces
that input, because a mean quietly taken over only the trials
that did not blow up describes a different, rosier model than
the one asked about. The number of trials must be positive
and a low above its high in any input is refused, because a
range that runs backward samples nothing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.sampling import SeededGenerator


@dataclass
class SimulationResult:
    trials: int
    mean: float
    minimum: float
    maximum: float
    percentiles: dict[int, float]


def _percentile(ordered: list[float], p: int) -> float:
    if not ordered:
        raise Invalid("no outcomes to take a percentile of")
    position = p / 100 * (len(ordered) - 1)
    low = int(position)
    frac = position - low
    if low + 1 < len(ordered):
        return (
            ordered[low]
            + frac * (ordered[low + 1] - ordered[low])
        )
    return ordered[low]


def simulate(
    model: Callable[[list[float]], float],
    ranges: list[tuple[float, float]],
    trials: int,
    seed: int,
    percentiles: tuple[int, ...] = (5, 50, 95),
) -> SimulationResult:
    if trials < 1:
        raise Invalid("a simulation needs at least one trial")
    for low, high in ranges:
        if low > high:
            raise Invalid(
                f"input range [{low}, {high}] runs backward "
                "and samples nothing"
            )
    generator = SeededGenerator(seed=seed)
    resolution = 1_000_000
    outcomes: list[float] = []
    for _ in range(trials):
        sample = []
        for low, high in ranges:
            unit = generator.next_int(resolution) / resolution
            sample.append(low + unit * (high - low))
        outcomes.append(model(sample))
    ordered = sorted(outcomes)
    return SimulationResult(
        trials=trials,
        mean=sum(outcomes) / trials,
        minimum=ordered[0],
        maximum=ordered[-1],
        percentiles={
            p: _percentile(ordered, p) for p in percentiles
        },
    )
