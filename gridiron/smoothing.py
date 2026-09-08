"""Exponential smoothing: forecasting from a weighted memory of the past.

Exponential smoothing forecasts a series by blending the last
observation with the last forecast, weighted by a factor
alpha between zero and one: a high alpha trusts recent data
and reacts fast, a low alpha trusts the established level and
reacts slowly, and the factor is the caller's judgment about
how much the world has changed, refused outside zero and one
because a weight outside that range is not a blend, it is an
extrapolation the method does not perform. Single smoothing
tracks a level and is right for a series with no trend; its
forecast for every future period is the same last level,
because a level-only model has no reason to expect the number
to move. Double smoothing adds a trend term, a second
smoothing of the level's changes, so its forecast climbs or
falls into the future the way the recent series did, which is
what a series with a slope needs and what single smoothing
gets wrong by flat-lining. The two are offered separately and
named rather than one function guessing whether a trend
exists, because that guess is a modeling decision. Both seed
the level from the first observation rather than zero, since
starting a smoother at zero makes its first several forecasts
climb out of a hole that is an artifact of the seed and not
the data. A series shorter than two points has nothing to
smooth and is refused.
"""

from __future__ import annotations

from gridiron.errors import Invalid


def _check_alpha(alpha: float, name: str) -> None:
    if not 0.0 <= alpha <= 1.0:
        raise Invalid(
            f"{name} {alpha} must sit in [0, 1]; a weight "
            "outside that is not a blend"
        )


def single(
    values: list[float], alpha: float
) -> list[float]:
    _check_alpha(alpha, "alpha")
    if not values:
        raise Invalid("no series to smooth")
    smoothed = [values[0]]
    for value in values[1:]:
        smoothed.append(
            alpha * value + (1 - alpha) * smoothed[-1]
        )
    return smoothed


def single_forecast(
    values: list[float], alpha: float
) -> float:
    return single(values, alpha)[-1]


def double(
    values: list[float], alpha: float, beta: float
) -> tuple[list[float], list[float]]:
    _check_alpha(alpha, "alpha")
    _check_alpha(beta, "beta")
    if len(values) < 2:
        raise Invalid(
            "double smoothing needs at least two points to "
            "establish a trend"
        )
    level = values[0]
    trend = values[1] - values[0]
    levels = [level]
    trends = [trend]
    for value in values[1:]:
        prev_level = level
        level = alpha * value + (1 - alpha) * (
            level + trend
        )
        trend = beta * (level - prev_level) + (
            1 - beta
        ) * trend
        levels.append(level)
        trends.append(trend)
    return levels, trends


def double_forecast(
    values: list[float],
    alpha: float,
    beta: float,
    ahead: int = 1,
) -> float:
    if ahead < 1:
        raise Invalid(
            "a forecast looks at least one period ahead"
        )
    levels, trends = double(values, alpha, beta)
    return levels[-1] + ahead * trends[-1]
