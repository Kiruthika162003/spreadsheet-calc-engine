"""The subtotal proof: hidden rows vanish from the fold, and grand skips section.

Two properties make SUBTOTAL worth its own function, and
this drill pins both against plain SUM standing beside it.
First, hidden rows do not participate: the same range summed
by SUM and by SUBTOTAL agrees when nothing is hidden and
diverges the moment a row is hidden, and the divergence is
the whole feature, so the drill asserts the two numbers are
equal before hiding and unequal after, with SUBTOTAL reading
only the visible rows. Second, a grand SUBTOTAL over a column
that already contains section SUBTOTALs counts each section
once, not twice, so a column of two section totals and a
grand total reads the grand as the sum of the sections, not
double it, which the self-blindness of the function
guarantees by skipping cells whose own formula is a
SUBTOTAL. The plain SUM in the same column, by contrast,
would double-count, and the drill records that it does,
because the contrast is the reason the self-blindness exists.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.subtotal import SubtotalScope, install


def _sum(sheet, scope, formula):
    return evaluate(
        parse_formula(formula),
        sheet.value_of,
        scope.table(full_table),
    )


def run() -> Finding:
    sheet = Engine().sheet
    for row, value in enumerate(
        (10.0, 20.0, 30.0, 40.0), start=1
    ):
        sheet.set_literal(
            CellRef(row=row, col=1), value
        )
    scope = SubtotalScope(sheet=sheet)
    plain_before = evaluate(
        parse_formula("=SUM(B2:B5)"),
        sheet.value_of,
        full_table,
    )
    sub_before = _sum(sheet, scope, "=SUBTOTAL(9, B2:B5)")
    scope.hide_rows([2, 3])
    sub_after = _sum(sheet, scope, "=SUBTOTAL(9, B2:B5)")
    plain_after = evaluate(
        parse_formula("=SUM(B2:B5)"),
        sheet.value_of,
        full_table,
    )

    nested = Engine()
    nsheet = nested.sheet
    nested_scope = SubtotalScope(sheet=nsheet)
    install(nested, nested_scope)
    for row, value in enumerate(
        (10.0, 20.0, 30.0, 40.0), start=1
    ):
        nested.set_literal(CellRef(row=row, col=1), value)
    nested.set_formula(
        CellRef.parse("B6"), "=SUBTOTAL(9, B1:B2)"
    )
    nested.set_formula(
        CellRef.parse("B7"), "=SUBTOTAL(9, B3:B4)"
    )
    nested.set_formula(
        CellRef.parse("B8"), "=SUBTOTAL(9, B1:B7)"
    )
    grand = nested.value(CellRef.parse("B8"))
    plain_double = evaluate(
        parse_formula("=SUM(B1:B7)"),
        nsheet.value_of,
        full_table,
    )

    numbers = {
        "plain_before": plain_before,
        "sub_before": sub_before,
        "agree_when_nothing_hidden": (
            plain_before == sub_before
        ),
        "sub_after_hiding": sub_after,
        "plain_after_hiding": plain_after,
        "diverge_after_hiding": (
            sub_after != plain_after
        ),
        "grand_skips_sections": grand,
        "plain_double_counts": plain_double,
    }
    holds = (
        plain_before == 100.0
        and sub_before == 100.0
        and sub_after == 50.0
        and plain_after == 100.0
        and grand == 100.0
        and plain_double == 160.0
    )
    return Finding(
        proof="subtotalproof",
        claim=(
            "SUBTOTAL agrees with SUM at 100 until rows hide, "
            "then reads the visible 50 while SUM stays 100, "
            "and a grand subtotal over two section subtotals "
            "reads 100 where plain SUM over the same column "
            "double-counts them to 160"
        ),
        numbers=numbers,
        holds=holds,
    )
