"""The table proof: the name follows the table, measured before and after.

The drill builds an orders table, registers it, and reads
SUM(ORDERS.AMOUNT) through the ordinary name table, then
adds a row and reads again without touching the formula. The
number worth watching is the difference between the two
reads: it must equal exactly the added amount, because the
name resolves against the live region and not a snapshot,
and a difference of zero would mean the oldest
quarterly-report bug in the book, the range that forgot to
grow, had survived the renovation. The second half drills
the refusal edge: an unknown table and an unknown column
both come back as #NAME? rather than raising, since a
formula speaking a name that does not exist is a data
condition for the grid, not a programming error for the
author, and the two kinds of failure must not swap coats.
The last number is the scalar boundary: the bare name in
scalar position still refuses with the range-in-scalar
lecture, proving the call-boundary unwrap did not quietly
legalize ranges everywhere.
"""

from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.tables import Table, TableRegistry
from gridiron.values import is_error


def run() -> Finding:
    sheet = Sheet()
    rows = (
        ("Item", "Amount"),
        ("Widget", 40.0),
        ("Gadget", 25.0),
        ("Cog", 60.0),
    )
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            sheet.set_literal(
                CellRef(row=row_index, col=col_index),
                value,
            )
    table = Table(
        name="Orders",
        sheet=sheet,
        region=RangeRef.parse("A1:B4"),
    )
    registry = TableRegistry()
    registry.add(table)
    formula = parse_formula("=SUM(ORDERS.AMOUNT)")

    def read() -> float:
        return evaluate(
            formula,
            sheet.value_of,
            full_table,
            registry.resolve,
        )

    before = read()
    table.add_row({"Item": "Sprocket", "Amount": 75.0})
    after = read()

    unknown_table = evaluate(
        parse_formula("=SUM(INVOICES.AMOUNT)"),
        sheet.value_of,
        full_table,
        registry.resolve,
    )
    unknown_column = evaluate(
        parse_formula("=SUM(ORDERS.COLOR)"),
        sheet.value_of,
        full_table,
        registry.resolve,
    )
    scalar_boundary = evaluate(
        parse_formula("=ORDERS.AMOUNT+1"),
        sheet.value_of,
        full_table,
        registry.resolve,
    )

    numbers = {
        "before": before,
        "after": after,
        "growth": after - before,
        "unknown_table_is_name_error": is_error(
            unknown_table
        )
        and unknown_table.code == "#NAME?",
        "unknown_column_is_name_error": is_error(
            unknown_column
        )
        and unknown_column.code == "#NAME?",
        "scalar_boundary_still_refuses": is_error(
            scalar_boundary
        )
        and scalar_boundary.code == "#VALUE!",
    }
    holds = (
        before == 125.0
        and after == 200.0
        and numbers["growth"] == 75.0
        and numbers["unknown_table_is_name_error"]
        and numbers["unknown_column_is_name_error"]
        and numbers["scalar_boundary_still_refuses"]
    )
    return Finding(
        proof="tableproof",
        claim=(
            "one added row grows the summed name by exactly "
            "the added amount with the formula untouched, "
            "unknown names stay #NAME? data conditions, and "
            "the bare name in scalar position still refuses"
        ),
        numbers=numbers,
        holds=holds,
    )
