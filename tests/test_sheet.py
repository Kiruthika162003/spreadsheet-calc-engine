from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


class TestStorage:
    def test_absence_is_the_dominant_state(self):
        sheet = Sheet()
        sheet.set_literal(ref("A1"), 5.0)
        sheet.set_formula(ref("B1"), "=A1*2")
        assert len(sheet.cells) == 2
        assert sheet.value_of(ref("ZZ999")) is None

    def test_the_formula_text_survives_verbatim(self):
        sheet = Sheet()
        sheet.set_formula(ref("B1"), "=a1  +  2")
        assert sheet.cell(ref("B1")).formula_text == "=a1  +  2"

    def test_formulas_parse_once_at_entry(self):
        sheet = Sheet()
        sheet.set_formula(ref("B1"), "=A1+2")
        assert sheet.cell(ref("B1")).tree is not None

    def test_setting_returns_the_displaced_cell(self):
        sheet = Sheet()
        sheet.set_literal(ref("A1"), 1.0)
        displaced = sheet.set_literal(ref("A1"), 2.0)
        assert displaced.literal == 1.0
        assert sheet.set_literal(ref("C9"), 1.0) is None

    def test_clear_returns_what_it_removed(self):
        sheet = Sheet()
        sheet.set_literal(ref("A1"), 7.0)
        assert sheet.clear(ref("A1")).literal == 7.0
        assert sheet.clear(ref("A1")) is None


class TestTheDeliberateBoundary:
    def test_an_equals_literal_is_routed_to_set_formula(self):
        sheet = Sheet()
        with pytest.raises(Invalid) as caught:
            sheet.set_literal(ref("A1"), "=A2")
        assert "stays deliberate" in str(caught.value)

    def test_a_formulaless_formula_is_refused(self):
        sheet = Sheet()
        with pytest.raises(Invalid) as caught:
            sheet.set_formula(ref("A1"), "42")
        assert "looks like a literal" in str(caught.value)


class TestTheCensus:
    def test_the_census_counts_both_kinds(self):
        sheet = Sheet()
        sheet.set_literal(ref("A1"), 1.0)
        sheet.set_literal(ref("A2"), 2.0)
        sheet.set_formula(ref("B1"), "=A1+A2")
        assert sheet.census().startswith(
            "3 occupied cell(s): 2 literal(s), 1 formula(s)"
        )

    def test_formula_cells_enumerate_in_grid_order(self):
        sheet = Sheet()
        sheet.set_formula(ref("C3"), "=1")
        sheet.set_formula(ref("A1"), "=2")
        found = [
            cell_ref.a1()
            for cell_ref, _ in sheet.formula_cells()
        ]
        assert found == ["A1", "C3"]
