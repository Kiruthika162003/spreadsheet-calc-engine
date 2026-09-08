"""Database functions: a query language made of two ranges and no strings attached.

The D-functions are the grid's oldest query engine: the
database range carries a header row and records, the
criteria range carries the same headers over condition rows,
and the shape of the criteria is the whole grammar,
conditions in one row AND together, separate rows OR
together. That convention is worth keeping because it is
visible on the sheet itself: an auditor reads the query by
looking at it, no formula archaeology required. Each
criterion cell reuses the same micro-grammar COUNTIF speaks,
parsed once by the criteria module, so ">100" and "app*"
mean the same thing in both worlds and there is exactly one
place wildcards are defined. The field argument accepts a
header name or a one-based column number, and every refusal
names what it saw: a field that is not in the header row
lists the row, a criteria header the database lacks is named
as the orphan it is, and DGET holds the strictest line in
the family, exactly one matching record or an error saying
how many it found, because get-me-the-value with three
answers is a coin flip wearing a suit.
"""

from __future__ import annotations

from gridiron.ast import Range
from gridiron.criteria import Criterion
from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.refs import CellRef
from gridiron.values import (
    ErrorValue,
    Value,
    is_error,
    render,
)


def _grid(region, lookup) -> list[list[Value]]:
    return [
        [
            lookup(CellRef(row=row, col=col))
            for col in range(region.left, region.right + 1)
        ]
        for row in range(region.top, region.bottom + 1)
    ]


def _headers(row: list[Value], what: str):
    names: list[str] = []
    for value in row:
        if not isinstance(value, str) or not value.strip():
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"the {what} range needs text headers in "
                    "its first row"
                ),
            )
        names.append(value.strip().upper())
    if len(set(names)) != len(names):
        return ErrorValue(
            code="#VALUE!",
            note=(
                f"the {what} headers repeat; an ambiguous "
                "column cannot be queried"
            ),
        )
    return names


def _tests_for(
    criteria_rows: list[list[Value]],
    criteria_headers: list[str],
    db_headers: list[str],
):
    all_rows: list[list[tuple[int, Criterion]]] = []
    for row in criteria_rows:
        tests: list[tuple[int, Criterion]] = []
        for index, cell in enumerate(row):
            if cell is None:
                continue
            if is_error(cell):
                return cell
            header = criteria_headers[index]
            if header not in db_headers:
                return ErrorValue(
                    code="#VALUE!",
                    note=(
                        f"the criteria column {header} is an "
                        "orphan; the database has no such "
                        "header"
                    ),
                )
            column = db_headers.index(header)
            if isinstance(cell, bool):
                return ErrorValue(
                    code="#VALUE!",
                    note=(
                        "boolean criteria are refused; write "
                        "the comparison out"
                    ),
                )
            source = (
                render(cell)
                if isinstance(cell, float)
                else cell
            )
            try:
                criterion = Criterion.parse(source)
            except Invalid as refusal:
                return ErrorValue(
                    code="#VALUE!", note=str(refusal)
                )
            tests.append((column, criterion))
        if tests:
            all_rows.append(tests)
    if not all_rows:
        return ErrorValue(
            code="#VALUE!",
            note=(
                "the criteria range has no condition; a "
                "query that matches everything should say "
                "so with a plain aggregate"
            ),
        )
    return all_rows


def _field_column(
    field_arg, lookup, functions, names, db_headers
):
    value = evaluate(field_arg, lookup, functions, names)
    if is_error(value):
        return value
    if isinstance(value, float) and not isinstance(
        value, bool
    ):
        index = int(value)
        if not 1 <= index <= len(db_headers):
            return ErrorValue(
                code="#VALUE!",
                note=(
                    f"field {index} is out of range; the "
                    f"database has {len(db_headers)} "
                    "column(s)"
                ),
            )
        return index - 1
    if isinstance(value, str):
        key = value.strip().upper()
        if key not in db_headers:
            row = ", ".join(db_headers)
            return ErrorValue(
                code="#VALUE!",
                note=f"no field named {value!r}; the header row has {row}",
            )
        return db_headers.index(key)
    return ErrorValue(
        code="#VALUE!",
        note="the field argument names a column or numbers one",
    )


def _matching_values(args, lookup, functions, names):
    if len(args) != 3 or not isinstance(
        args[0], Range
    ) or not isinstance(args[2], Range):
        return ErrorValue(
            code="#VALUE!",
            note=(
                "a database function takes a database range, "
                "a field, and a criteria range"
            ),
        )
    database = _grid(args[0].ref, lookup)
    criteria = _grid(args[2].ref, lookup)
    if len(database) < 2:
        return ErrorValue(
            code="#VALUE!",
            note="the database needs a header row and records",
        )
    db_headers = _headers(database[0], "database")
    if is_error(db_headers):
        return db_headers
    criteria_headers = _headers(criteria[0], "criteria")
    if is_error(criteria_headers):
        return criteria_headers
    column = _field_column(
        args[1], lookup, functions, names, db_headers
    )
    if is_error(column):
        return column
    tests = _tests_for(
        criteria[1:], criteria_headers, db_headers
    )
    if is_error(tests):
        return tests
    matched: list[Value] = []
    for record in database[1:]:
        hit = any(
            all(
                criterion.matches(record[col])
                for col, criterion in row_tests
            )
            for row_tests in tests
        )
        if hit:
            matched.append(record[column])
    return matched


def _fold(agg: str):
    def run(args, lookup, functions, names) -> Value:
        values = _matching_values(
            args, lookup, functions, names
        )
        if is_error(values):
            return values
        for value in values:
            if is_error(value):
                return value
        numbers = [
            v
            for v in values
            if isinstance(v, float)
            and not isinstance(v, bool)
        ]
        if agg == "DCOUNT":
            return float(len(numbers))
        if not numbers:
            return ErrorValue(
                code="#DIV/0!"
                if agg == "DAVERAGE"
                else "#NUM!",
                note=(
                    f"{agg} matched no numeric values; the "
                    "query found nothing to fold"
                ),
            )
        if agg == "DSUM":
            return sum(numbers)
        if agg == "DAVERAGE":
            return sum(numbers) / len(numbers)
        if agg == "DMIN":
            return min(numbers)
        return max(numbers)

    return run


def _dget(args, lookup, functions, names) -> Value:
    values = _matching_values(args, lookup, functions, names)
    if is_error(values):
        return values
    if len(values) == 0:
        return ErrorValue(
            code="#VALUE!",
            note="no record matches; DGET has nothing to get",
        )
    if len(values) > 1:
        return ErrorValue(
            code="#NUM!",
            note=(
                f"{len(values)} records match; DGET needs "
                "exactly one, because get-me-the-value with "
                "several answers is a coin flip"
            ),
        )
    return values[0]


QUERY_FUNCTIONS = {
    "DSUM": _fold("DSUM"),
    "DAVERAGE": _fold("DAVERAGE"),
    "DCOUNT": _fold("DCOUNT"),
    "DMIN": _fold("DMIN"),
    "DMAX": _fold("DMAX"),
    "DGET": _dget,
}
