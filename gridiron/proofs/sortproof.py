"""The sort proof: rows travel whole, empties sink, formulas refuse to ride.

The drill sorts a three-column table by its middle column
and checks the property that matters most and is easiest to
break: rows move as units. It plants a distinctive marker in
the third column of each row before sorting and confirms
each marker still sits beside the key it started with,
because a sort that permutes columns independently passes a
key-order check while scrambling every record, the silent
corruption this proof exists to catch. Empties in the key
column must sink to the bottom whichever direction the sort
runs, so the drill sorts ascending and descending and
confirms the blank row lands last both times. The last check
is the formula refusal: a range holding even one formula
cell refuses to sort by name, because moving a formula
rewrites what its relative references mean, and the number
worth reading there is that the refusal fires before any
cell has moved, leaving the range exactly as it was.
"""

from __future__ import annotations

from gridiron.errors import Invalid
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.sorting import Sorter


def _table() -> Sheet:
    sheet = Sheet()
    rows = (
        ("east", 30.0, "r-east"),
        ("west", 10.0, "r-west"),
        ("north", None, "r-north"),
        ("south", 20.0, "r-south"),
    )
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            if value is not None:
                sheet.set_literal(
                    CellRef(row=row_index, col=col_index),
                    value,
                )
    return sheet


def _marker_pairs(sheet: Sheet) -> list[tuple[float, str]]:
    pairs = []
    for row in range(4):
        key = sheet.value_of(CellRef(row=row, col=1))
        marker = sheet.value_of(CellRef(row=row, col=2))
        pairs.append((key, marker))
    return pairs


def run() -> Finding:
    region = RangeRef.parse("A1:C4")

    ascending = _table()
    Sorter(sheet=ascending).sort_range(region, key_col=1)
    asc_pairs = _marker_pairs(ascending)

    descending = _table()
    Sorter(sheet=descending).sort_range(
        region, key_col=1, descending=True
    )
    desc_pairs = _marker_pairs(descending)

    rows_traveled_whole = all(
        (key is None)
        or marker == f"r-{_name_for(key)}"
        for key, marker in asc_pairs
        if marker is not None
    )
    blank_sinks_ascending = asc_pairs[-1][0] is None
    blank_sinks_descending = desc_pairs[-1][0] is None

    formula_sheet = _table()
    formula_sheet.set_formula(
        CellRef.parse("B2"), "=10+10"
    )
    before = formula_sheet.value_of(CellRef.parse("A1"))
    refused = False
    try:
        Sorter(sheet=formula_sheet).sort_range(
            region, key_col=1
        )
    except Invalid:
        refused = True
    untouched = (
        formula_sheet.value_of(CellRef.parse("A1")) == before
    )

    numbers = {
        "ascending_keys": [p[0] for p in asc_pairs],
        "descending_keys": [p[0] for p in desc_pairs],
        "rows_traveled_whole": rows_traveled_whole,
        "blank_sinks_both_ways": (
            blank_sinks_ascending and blank_sinks_descending
        ),
        "formula_refused_before_moving": refused
        and untouched,
    }
    holds = (
        numbers["ascending_keys"] == [10.0, 20.0, 30.0, None]
        and numbers["descending_keys"]
        == [30.0, 20.0, 10.0, None]
        and rows_traveled_whole
        and numbers["blank_sinks_both_ways"]
        and numbers["formula_refused_before_moving"]
    )
    return Finding(
        proof="sortproof",
        claim=(
            "a sort moves whole rows so each marker stays "
            "beside its key, empties sink to the bottom "
            "both directions, and a formula in the range "
            "refuses the sort before any cell has moved"
        ),
        numbers=numbers,
        holds=holds,
    )


def _name_for(key: float) -> str:
    return {10.0: "west", 20.0: "south", 30.0: "east"}[key]
