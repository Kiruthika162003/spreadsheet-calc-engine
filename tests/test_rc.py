from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.paste import shifted_formula
from gridiron.rc import (
    formula_to_r1c1,
    ref_from_r1c1,
    ref_to_r1c1,
)
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


class TestReferenceSpelling:
    def test_the_cell_to_my_left(self):
        assert (
            ref_to_r1c1(ref("A5"), origin=ref("B5"))
            == "RC[-1]"
        )

    def test_my_own_cell_is_bare(self):
        assert ref_to_r1c1(ref("C3"), origin=ref("C3")) == "RC"

    def test_dollars_become_numbers(self):
        assert (
            ref_to_r1c1(ref("$C$5"), origin=ref("A1"))
            == "R5C3"
        )

    def test_a_mixed_pin_mixes_the_grammar(self):
        assert (
            ref_to_r1c1(ref("C$5"), origin=ref("A1"))
            == "R5C[2]"
        )

    def test_round_trips_keep_the_dollars(self):
        for spelling in ("A1", "$A1", "A$1", "$A$1"):
            original = ref(spelling)
            spoken = ref_to_r1c1(original, origin=ref("D7"))
            back = ref_from_r1c1(spoken, origin=ref("D7"))
            assert back == original


class TestParsingBack:
    def test_offsets_walk_from_the_origin(self):
        assert ref_from_r1c1(
            "R[2]C[-1]", origin=ref("C3")
        ) == ref("B5")

    def test_absolutes_land_where_numbered(self):
        parsed = ref_from_r1c1("R5C3", origin=ref("Z99"))
        assert parsed.a1() == "$C$5"

    def test_gibberish_is_refused_with_the_grammar(self):
        with pytest.raises(Invalid) as caught:
            ref_from_r1c1("Q7", origin=ref("A1"))
        assert "grammar is R and C" in str(caught.value)

    def test_walking_off_the_edge_is_named(self):
        with pytest.raises(Invalid) as caught:
            ref_from_r1c1("R[-3]C", origin=ref("A2"))
        assert "walks off the sheet's edge" in str(
            caught.value
        )


class TestTheCopyInvariance:
    def test_a_copied_column_collapses_to_one_string(self):
        spellings = {
            formula_to_r1c1("=A2*1.19", ref("B2")),
            formula_to_r1c1("=A3*1.19", ref("B3")),
            formula_to_r1c1("=A9*1.19", ref("B9")),
        }
        assert spellings == {"=(RC[-1]*1.19)"}

    def test_shifting_never_changes_the_spelling(self):
        formula = "=SUM(A1:A3)+$B$1"
        home = ref("C5")
        spoken = formula_to_r1c1(formula, home)
        for rows, cols in ((1, 0), (10, 3), (0, 7)):
            moved = shifted_formula(formula, rows, cols)
            there = CellRef(
                row=home.row + rows, col=home.col + cols
            )
            assert formula_to_r1c1(moved, there) == spoken

    def test_the_absolute_half_stays_pinned(self):
        spoken = formula_to_r1c1("=A$1+$A2", ref("C3"))
        assert spoken == "=(R1C[-2]+R[-1]C1)"

    def test_cross_sheet_references_keep_their_sheet(self):
        spoken = formula_to_r1c1("=Data!B1*2", ref("C2"))
        assert spoken == "=(DATA!R[-1]C[-1]*2)"
