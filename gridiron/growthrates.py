"""Growth rates: the period changes, and the single rate that summarizes them.

A series of values invites three growth questions, and the
trap is answering the third with the wrong average. The
period-over-period rates are each value over the previous
minus one, undefined where the previous value is zero,
reported absent there rather than as an infinite jump. The
average growth rate is where the mistake lives: the honest
summary of a sequence of growth rates is the geometric mean,
not the arithmetic one, because growth compounds and the
arithmetic mean of plus-fifty-percent then minus-fifty-
percent is zero while the money is down twenty-five percent,
a lie the geometric mean does not tell. So the average here
is geometric, computed as the CAGR of the endpoints, and it
equals the compound rate that would carry the first value to
the last over the periods between them. That equality is the
point and the tests hold to it: the average of the period
rates and the CAGR of the endpoints are the same number,
because they are two descriptions of one compounding. CAGR
needs positive endpoints, refused otherwise, because a
compound rate from or to a non-positive value is a root of a
negative, and a series that crosses zero has no single
compound rate, only a story the period rates tell one step
at a time. A series shorter than two points has no growth to
measure and is refused.
"""

from __future__ import annotations

from gridiron.errors import Invalid

Number = float | None


def period_rates(values: list[float]) -> list[Number]:
    if len(values) < 2:
        raise Invalid(
            "growth needs at least two values to compare"
        )
    rates: list[Number] = []
    for index in range(1, len(values)):
        previous = values[index - 1]
        if previous == 0:
            rates.append(None)
        else:
            rates.append(values[index] / previous - 1)
    return rates


def cagr(values: list[float]) -> float:
    if len(values) < 2:
        raise Invalid(
            "CAGR needs at least two values"
        )
    begin, end = values[0], values[-1]
    if begin <= 0 or end <= 0:
        raise Invalid(
            "CAGR needs positive endpoints; a series that "
            "crosses zero has no single compound rate, only "
            "the story the period rates tell"
        )
    periods = len(values) - 1
    return (end / begin) ** (1 / periods) - 1


def average_growth(values: list[float]) -> float:
    # The geometric mean of the period growth factors is the
    # CAGR of the endpoints; computing it that way avoids a
    # product that could underflow on a long series.
    return cagr(values)


def total_growth(values: list[float]) -> float:
    if len(values) < 2:
        raise Invalid("growth needs at least two values")
    if values[0] == 0:
        raise Invalid(
            "total growth from zero is undefined"
        )
    return values[-1] / values[0] - 1
