from __future__ import annotations

import pytest

from gridiron.criteria import Criterion
from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.filters import FilterView
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.subtotal import SubtotalScope, install


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def ledger() -> Sheet:
    sheet = Sheet()
    for address, value in (
        ("A1", "Region"),
        ("B1", "Sales"),
        ("A2", "East"),
        ("B2", 100.0),
        ("A3", "West"),
        ("B3", 40.0),
        ("A4", "East"),
        ("B4", 60.0),
        ("A5", "West"),
        ("B5", 200.0),
    ):
        sheet.set_literal(ref(address), value)
    return sheet


def run(sheet: Sheet, scope: SubtotalScope, formula: str):
    return evaluate(
        parse_formula(formula),
        sheet.value_of,
        scope.table(full_table),
    )


class TestTheView:
    def test_everything_visible_matches_sum(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        assert run(
            sheet, scope, "=SUBTOTAL(9, B2:B5)"
        ) == 400.0

    def test_hidden_rows_do_not_participate(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        scope.hide_rows([2, 4])
        assert run(
            sheet, scope, "=SUBTOTAL(9, B2:B5)"
        ) == 160.0
        assert run(
            sheet, scope, "=SUBTOTAL(2, B2:B5)"
        ) == 2.0

    def test_a_filter_view_is_adopted(self):
        sheet = ledger()
        view = FilterView(
            sheet=sheet, region=RangeRef.parse("A1:B5")
        )
        view.column_criteria[0] = Criterion.parse("East")
        scope = SubtotalScope(sheet=sheet)
        verdict = scope.adopt_filter(view)
        assert "2 filtered row(s) adopted" in verdict
        assert run(
            sheet, scope, "=SUBTOTAL(9, B2:B5)"
        ) == 160.0

    def test_plain_sum_stays_blind_on_purpose(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        scope.hide_rows([2])
        assert run(sheet, scope, "=SUM(B2:B5)") == 400.0

    def test_unhide_restores_the_full_fold(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        scope.hide_rows([2, 3])
        assert "2 row(s) returned" in scope.unhide_all()
        assert run(
            sheet, scope, "=SUBTOTAL(9, B2:B5)"
        ) == 400.0


class TestSelfBlindness:
    def test_a_grand_subtotal_skips_section_subtotals(self):
        sheet = ledger()
        engine = Engine(sheet=sheet)
        scope = SubtotalScope(sheet=sheet)
        install(engine, scope)
        engine.set_formula(
            ref("B6"), "=SUBTOTAL(9, B2:B3)"
        )
        engine.set_formula(
            ref("B7"), "=SUBTOTAL(9, B4:B5)"
        )
        engine.set_formula(
            ref("B8"), "=SUBTOTAL(9, B2:B7)"
        )
        assert engine.value(ref("B6")) == 140.0
        assert engine.value(ref("B7")) == 260.0
        assert engine.value(ref("B8")) == 400.0

    def test_a_wrapped_subtotal_counts_as_a_plain_value(self):
        sheet = ledger()
        engine = Engine(sheet=sheet)
        scope = SubtotalScope(sheet=sheet)
        install(engine, scope)
        engine.set_formula(
            ref("B6"), "=SUBTOTAL(9, B2:B5)+0"
        )
        engine.set_formula(
            ref("B7"), "=SUBTOTAL(9, B2:B6)"
        )
        assert engine.value(ref("B7")) == 800.0


class TestRefusals:
    def test_an_unknown_code_quotes_the_menu(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        outcome = run(sheet, scope, "=SUBTOTAL(7, B2:B5)")
        assert outcome.code == "#VALUE!"
        assert "9 SUM" in outcome.note

    def test_a_scalar_second_argument_is_refused(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        outcome = run(sheet, scope, "=SUBTOTAL(9, B2)")
        assert outcome.code == "#VALUE!"
        assert "a code and a range" in outcome.note

    def test_averaging_a_fully_hidden_view_divides_by_zero(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        scope.hide_rows([1, 2, 3, 4])
        outcome = run(sheet, scope, "=SUBTOTAL(1, B2:B5)")
        assert outcome.code == "#DIV/0!"

    def test_installing_across_sheets_is_refused(self):
        engine = Engine(sheet=ledger())
        scope = SubtotalScope(sheet=Sheet())
        with pytest.raises(Invalid) as caught:
            install(engine, scope)
        assert "wrong rows" in str(caught.value)

    def test_other_names_pass_through_untouched(self):
        sheet = ledger()
        scope = SubtotalScope(sheet=sheet)
        assert run(
            sheet, scope, "=MAX(B2:B5)"
        ) == 200.0
