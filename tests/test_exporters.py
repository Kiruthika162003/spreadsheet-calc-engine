from __future__ import annotations

import json

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.exporters import Exporter
from gridiron.refs import CellRef, RangeRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def stocked_engine() -> Engine:
    engine = Engine()
    for address, value in (
        ("A1", "Item"),
        ("B1", "Qty"),
        ("C1", "Note"),
        ("A2", "Widget <A>"),
        ("B2", 2.0),
        ("C2", "fast & loose"),
        ("A3", "Gadget"),
        ("B3", 10.0),
    ):
        engine.set_literal(ref(address), value)
    return engine


def exporter(engine: Engine | None = None) -> Exporter:
    engine = engine or stocked_engine()
    return Exporter(
        sheet=engine.sheet,
        region=RangeRef.parse("A1:C3"),
    )


class TestMarkdown:
    def test_numeric_columns_align_right(self):
        lines = exporter().to_markdown().splitlines()
        assert lines[0] == "| Item | Qty | Note |"
        assert lines[1] == "| :--- | ---: | :--- |"
        assert lines[2] == (
            "| Widget <A> | 2 | fast & loose |"
        )

    def test_an_empty_cell_stays_empty(self):
        lines = exporter().to_markdown().splitlines()
        assert lines[3] == "| Gadget | 10 |  |"

    def test_an_error_exports_as_its_code(self):
        engine = stocked_engine()
        engine.set_formula(ref("B3"), "=1/0")
        markdown = exporter(engine).to_markdown()
        assert "#DIV/0!" in markdown
        lines = markdown.splitlines()
        assert lines[1] == "| :--- | :--- | :--- |"


class TestHtml:
    def test_the_three_breakers_are_escaped(self):
        html = exporter().to_html()
        assert "Widget &lt;A&gt;" in html
        assert "fast &amp; loose" in html
        assert "<A>" not in html

    def test_numeric_cells_carry_the_class(self):
        html = exporter().to_html()
        assert '<td class="num">2</td>' in html
        assert '<td class="num">Widget' not in html

    def test_the_table_nests_properly(self):
        html = exporter().to_html()
        assert html.startswith("<table>")
        assert html.endswith("</table>")
        assert html.index("<thead>") < html.index("<tbody>")


class TestRecords:
    def test_rows_key_by_header_in_order(self):
        records = exporter().to_records()
        assert records[0] == {
            "Item": "Widget <A>",
            "Qty": 2.0,
            "Note": "fast & loose",
        }
        assert list(records[0]) == ["Item", "Qty", "Note"]

    def test_an_error_becomes_a_tagged_object(self):
        engine = stocked_engine()
        engine.set_formula(ref("B2"), "=1/0")
        records = exporter(engine).to_records()
        assert records[0]["Qty"] == {"error": "#DIV/0!"}

    def test_json_round_trips_through_the_standard_library(self):
        text = exporter().to_json()
        parsed = json.loads(text)
        assert parsed[1]["Item"] == "Gadget"
        assert parsed[1]["Note"] is None


class TestRefusals:
    def test_duplicate_headers_are_refused(self):
        engine = stocked_engine()
        engine.set_literal(ref("C1"), "Item")
        with pytest.raises(Invalid) as caught:
            exporter(engine).to_markdown()
        assert "quietly ate a column" in str(caught.value)

    def test_a_missing_header_is_a_rumor(self):
        engine = stocked_engine()
        engine.clear(ref("C1"))
        with pytest.raises(Invalid) as caught:
            exporter(engine).to_records()
        assert "rumor in a report" in str(caught.value)
