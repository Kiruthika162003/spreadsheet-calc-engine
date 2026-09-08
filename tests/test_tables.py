from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.tables import Table, TableRegistry
from gridiron.values import is_error


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def orders_sheet() -> Sheet:
    sheet = Sheet()
    rows = (
        ("Item", "Qty", "Amount"),
        ("Widget", 2.0, 40.0),
        ("Gadget", 1.0, 25.0),
        ("Widget", 3.0, 60.0),
    )
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            sheet.set_literal(
                CellRef(row=row_index, col=col_index), value
            )
    return sheet


def orders_table(sheet: Sheet | None = None) -> Table:
    return Table(
        name="Orders",
        sheet=sheet or orders_sheet(),
        region=RangeRef.parse("A1:C4"),
    )


class TestTheTableShape:
    def test_columns_read_from_the_header_row(self):
        assert orders_table().columns() == [
            "ITEM",
            "QTY",
            "AMOUNT",
        ]

    def test_a_headerless_table_is_refused(self):
        sheet = orders_sheet()
        sheet.set_literal(ref("B1"), 7.0)
        with pytest.raises(Invalid) as caught:
            orders_table(sheet)
        assert "needs text headers" in str(caught.value)

    def test_a_bodyless_table_has_ambitions(self):
        with pytest.raises(Invalid) as caught:
            Table(
                name="Empty",
                sheet=orders_sheet(),
                region=RangeRef.parse("A1:C1"),
            )
        assert "range with ambitions" in str(caught.value)

    def test_column_values_skip_the_header(self):
        assert orders_table().column_values("Amount") == [
            40.0,
            25.0,
            60.0,
        ]


class TestGrowth:
    def test_a_row_lands_under_the_body(self):
        table = orders_table()
        verdict = table.add_row(
            {"Item": "Sprocket", "Amount": 15.0}
        )
        assert "grew to row 5" in verdict
        assert "2 of 3 column(s) filled" in verdict
        assert table.column_values("Amount")[-1] == 15.0
        assert table.column_values("Qty")[-1] is None

    def test_an_unknown_column_quotes_the_header_row(self):
        with pytest.raises(Invalid) as caught:
            orders_table().add_row({"Color": "red"})
        assert "ITEM, QTY, AMOUNT" in str(caught.value)


class TestTotals:
    def test_each_column_folds_its_own_way(self):
        totals = orders_table().totals(
            {"Qty": "SUM", "Amount": "AVERAGE"}
        )
        assert totals["QTY"] == 6.0
        assert totals["AMOUNT"] == pytest.approx(125.0 / 3)

    def test_an_error_poisons_only_its_column(self):
        sheet = orders_sheet()
        table = orders_table(sheet)
        engine_error = evaluate(
            parse_formula("=1/0"),
            sheet.value_of,
            full_table,
        )
        sheet.set_literal(ref("C3"), engine_error)
        totals = table.totals(
            {"Qty": "SUM", "Amount": "SUM"}
        )
        assert totals["QTY"] == 6.0
        assert is_error(totals["AMOUNT"])

    def test_an_unknown_aggregation_lists_the_menu(self):
        with pytest.raises(Invalid) as caught:
            orders_table().totals({"Qty": "MODE"})
        assert "SUM, COUNT, AVERAGE, MIN, or MAX" in str(
            caught.value
        )


class TestTheNameBridge:
    def test_formulas_speak_the_dot_form(self):
        sheet = orders_sheet()
        registry = TableRegistry()
        registry.add(orders_table(sheet))
        outcome = evaluate(
            parse_formula("=SUM(ORDERS.AMOUNT)"),
            sheet.value_of,
            full_table,
            registry.resolve,
        )
        assert outcome == 125.0

    def test_the_name_follows_the_table_not_the_snapshot(self):
        sheet = orders_sheet()
        table = orders_table(sheet)
        registry = TableRegistry()
        registry.add(table)
        formula = parse_formula("=SUM(ORDERS.AMOUNT)")
        before = evaluate(
            formula,
            sheet.value_of,
            full_table,
            registry.resolve,
        )
        table.add_row({"Item": "Cog", "Amount": 75.0})
        after = evaluate(
            formula,
            sheet.value_of,
            full_table,
            registry.resolve,
        )
        assert before == 125.0
        assert after == 200.0

    def test_an_unknown_table_or_column_stays_a_name_error(self):
        sheet = orders_sheet()
        registry = TableRegistry()
        registry.add(orders_table(sheet))
        for formula in (
            "=SUM(INVOICES.AMOUNT)",
            "=SUM(ORDERS.COLOR)",
        ):
            outcome = evaluate(
                parse_formula(formula),
                sheet.value_of,
                full_table,
                registry.resolve,
            )
            assert outcome.code == "#NAME?"

    def test_colliding_table_names_are_refused(self):
        registry = TableRegistry()
        registry.add(orders_table())
        with pytest.raises(Invalid) as caught:
            registry.add(orders_table())
        assert "name table that lies" in str(caught.value)
