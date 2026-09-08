"""COUNTIF, SUMIF, AVERAGEIF: the criterion decides, the region pays.

The conditional aggregates walk a region, apply one compiled
criterion, and fold the survivors. SUMIF's third argument is
the shape trap the family is famous for: the sum region is
allowed to differ from the test region, offset row by row,
and the two regions must agree in size, because the
incumbent's behavior of silently extending the sum region to
match is the kind of helpfulness that moves money between
quarters. Here mismatched shapes are a #VALUE! naming both
sizes. Empty cells never match any criterion, errors in the
tested region poison the whole aggregate rather than being
skipped, and AVERAGEIF of zero survivors is the division
error it is, with the criterion quoted so the formula bar
answers the question before it is asked.
"""

from __future__ import annotations

from gridiron.ast import Range, Text
from gridiron.criteria import Criterion
from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
)


def _criterion(args, index, lookup, functions, names):
    if isinstance(args[index], Text):
        source = args[index].value
    else:
        value = evaluate(
            args[index], lookup, functions, names
        )
        if is_error(value):
            return value
        if isinstance(value, float):
            source = (
                str(int(value))
                if value == int(value)
                else str(value)
            )
        else:
            source = str(value)
    try:
        return Criterion.parse(source)
    except Invalid as refusal:
        return ErrorValue(
            code="#VALUE!", note=str(refusal)
        )


def _region_values(
    region_arg, lookup
) -> list[Value] | ErrorValue:
    if not isinstance(region_arg, Range):
        return ErrorValue(
            code="#VALUE!",
            note="the tested argument must be a range",
        )
    values: list[Value] = []
    for cell in region_arg.ref.cells():
        value = lookup(cell)
        if is_error(value):
            return value
        values.append(value)
    return values


def _countif(args, lookup, functions, names) -> Value:
    if len(args) != 2:
        return ErrorValue(
            code="#VALUE!",
            note="COUNTIF takes a range and a criterion",
        )
    values = _region_values(args[0], lookup)
    if is_error(values):
        return values
    criterion = _criterion(args, 1, lookup, functions, names)
    if is_error(criterion):
        return criterion
    return float(
        sum(1 for value in values if criterion.matches(value))
    )


def _paired_regions(args, lookup):
    tested = _region_values(args[0], lookup)
    if is_error(tested):
        return tested
    if len(args) == 3:
        if not isinstance(args[2], Range):
            return ErrorValue(
                code="#VALUE!",
                note="the fold region must be a range",
            )
        folded = _region_values(args[2], lookup)
        if is_error(folded):
            return folded
        if len(folded) != len(tested):
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"the tested region holds {len(tested)} "
                    f"cell(s) and the fold region "
                    f"{len(folded)}; silently extending one "
                    "moves money between quarters"
                ),
            )
        return tested, folded
    return tested, tested


def _sumif(args, lookup, functions, names) -> Value:
    if len(args) not in (2, 3):
        return ErrorValue(
            code="#VALUE!",
            note="SUMIF takes range, criterion, optional fold",
        )
    regions = _paired_regions(args, lookup)
    if is_error(regions):
        return regions
    tested, folded = regions
    criterion = _criterion(args, 1, lookup, functions, names)
    if is_error(criterion):
        return criterion
    total = 0.0
    for probe, value in zip(tested, folded, strict=True):
        if criterion.matches(probe) and isinstance(
            value, float
        ):
            total += value
    return total


def _averageif(args, lookup, functions, names) -> Value:
    if len(args) not in (2, 3):
        return ErrorValue(
            code="#VALUE!",
            note="AVERAGEIF takes range, criterion, optional fold",
        )
    regions = _paired_regions(args, lookup)
    if is_error(regions):
        return regions
    tested, folded = regions
    criterion = _criterion(args, 1, lookup, functions, names)
    if is_error(criterion):
        return criterion
    survivors = [
        value
        for probe, value in zip(tested, folded, strict=True)
        if criterion.matches(probe)
        and isinstance(value, float)
    ]
    if not survivors:
        return ErrorValue(
            code="#DIV/0!",
            note=(
                f"no cell satisfied {criterion.source!r}; the "
                "formula bar answers before it is asked"
            ),
        )
    return sum(survivors) / len(survivors)


CONDITIONAL_FUNCTIONS = {
    "COUNTIF": _countif,
    "SUMIF": _sumif,
    "AVERAGEIF": _averageif,
}
