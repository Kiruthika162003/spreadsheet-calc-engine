"""CONVERT: unit conversion where temperature refuses to be a ratio.

Most unit conversion is multiplication by a ratio, and the
temptation is to build one table of factors and divide, which
works for length and mass and time and breaks silently for
temperature. Celsius to Fahrenheit is affine, not linear:
zero Celsius is thirty-two Fahrenheit, so scaling by a ratio
turns freezing into absolute cold and nobody notices until
the thermostat model is wrong. This module keeps temperature
in its own affine world with explicit offsets and treats
every other family as ratios against a base unit, so a
conversion is two steps, into the base and out to the target,
and mixing families, meters to grams, is refused by name
rather than returning a number that means nothing. The base
unit per family is arbitrary but fixed and documented, and
the ratios are exact where the definition is exact, a foot is
0.3048 meters by treaty not measurement, and stated as such.
An unknown unit is refused with the unit quoted, because a
CONVERT that guessed at an unrecognized abbreviation would
be the most confident wrong answer in the workbook.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    to_number,
)

_RATIOS = {
    "length": {
        "m": 1.0,
        "km": 1000.0,
        "cm": 0.01,
        "mm": 0.001,
        "mi": 1609.344,
        "yd": 0.9144,
        "ft": 0.3048,
        "in": 0.0254,
    },
    "mass": {
        "g": 1.0,
        "kg": 1000.0,
        "mg": 0.001,
        "lbm": 453.59237,
        "oz": 28.349523125,
    },
    "time": {
        "sec": 1.0,
        "min": 60.0,
        "hr": 3600.0,
        "day": 86400.0,
    },
}

# Temperature is affine: value in base kelvin = value * scale
# + offset, and back out the reverse.
_TEMPERATURE = {
    "K": (1.0, 0.0),
    "C": (1.0, 273.15),
    "F": (5.0 / 9.0, 459.67 * 5.0 / 9.0),
}


def _family_of(unit: str) -> str | None:
    for family, table in _RATIOS.items():
        if unit in table:
            return family
    if unit in _TEMPERATURE:
        return "temperature"
    return None


def _convert(
    amount: float, source: str, target: str
) -> Value:
    source_family = _family_of(source)
    target_family = _family_of(target)
    if source_family is None:
        return ErrorValue(
            code="#N/A",
            note=f"unknown unit {source!r}",
        )
    if target_family is None:
        return ErrorValue(
            code="#N/A",
            note=f"unknown unit {target!r}",
        )
    if source_family != target_family:
        return ErrorValue(
            code="#N/A",
            note=(
                f"{source!r} is {source_family} and "
                f"{target!r} is {target_family}; converting "
                "across families returns a number that means "
                "nothing"
            ),
        )
    if source_family == "temperature":
        scale_in, offset_in = _TEMPERATURE[source]
        kelvin = amount * scale_in + offset_in
        scale_out, offset_out = _TEMPERATURE[target]
        return (kelvin - offset_out) / scale_out
    table = _RATIOS[source_family]
    return amount * table[source] / table[target]


def convert_function(args, lookup, functions, names) -> Value:
    if len(args) != 3:
        return ErrorValue(
            code="#VALUE!",
            note="CONVERT takes an amount, a from-unit, "
            "and a to-unit",
        )
    amount = to_number(
        evaluate(args[0], lookup, functions, names)
    )
    if is_error(amount):
        return amount
    source = evaluate(args[1], lookup, functions, names)
    target = evaluate(args[2], lookup, functions, names)
    for unit in (source, target):
        if is_error(unit):
            return unit
        if not isinstance(unit, str):
            return ErrorValue(
                code="#VALUE!",
                note="CONVERT units are text abbreviations",
            )
    return _convert(amount, source, target)


UNIT_FUNCTIONS = {
    "CONVERT": convert_function,
}
