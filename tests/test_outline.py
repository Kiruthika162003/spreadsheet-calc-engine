from __future__ import annotations

import pytest

from gridiron.errors import Invalid, Missing
from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.outline import Outline
from gridiron.parser import parse_formula
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.subtotal import SubtotalScope


class TestStructure:
    def test_nested_groups_are_legal(self):
        outline = Outline()
        outline.group_rows(1, 10)
        outline.group_rows(2, 5)
        assert outline.level_of(3) == 2
        assert outline.level_of(8) == 1
        assert outline.level_of(0) == 0

    def test_disjoint_groups_are_legal(self):
        outline = Outline()
        outline.group_rows(1, 4)
        outline.group_rows(6, 9)
        assert outline.census().startswith("2 group(s)")

    def test_a_braid_is_refused_at_creation(self):
        outline = Outline()
        outline.group_rows(1, 6)
        with pytest.raises(Invalid) as caught:
            outline.group_rows(4, 9)
        assert "braided" in str(caught.value)

    def test_a_duplicate_group_is_named(self):
        outline = Outline()
        outline.group_rows(1, 4)
        with pytest.raises(Invalid) as caught:
            outline.group_rows(1, 4)
        assert "already exists" in str(caught.value)


class TestCollapse:
    def test_collapsing_hides_the_whole_span(self):
        outline = Outline()
        outline.group_rows(2, 5)
        verdict = outline.collapse(2, 5)
        assert "4 row(s) now hidden" in verdict
        assert outline.visible_rows(0, 7) == [0, 1, 6, 7]

    def test_children_remember_their_state(self):
        outline = Outline()
        outline.group_rows(1, 10)
        outline.group_rows(2, 4)
        outline.collapse(2, 4)
        outline.collapse(1, 10)
        outline.expand(1, 10)
        assert outline.hidden_rows() == {2, 3, 4}

    def test_expanding_the_never_grouped_is_missing(self):
        outline = Outline()
        with pytest.raises(Missing):
            outline.expand(3, 7)

    def test_the_census_reads_in_one_line(self):
        outline = Outline()
        outline.group_rows(1, 10)
        outline.group_rows(2, 4)
        outline.collapse(2, 4)
        assert outline.census() == (
            "2 group(s), max depth 2, 3 row(s) hidden"
        )


class TestTheSubtotalBridge:
    def test_a_subtotal_sums_the_visible_story(self):
        sheet = Sheet()
        for row, value in enumerate(
            (10.0, 20.0, 30.0, 40.0), start=1
        ):
            sheet.set_literal(
                CellRef(row=row, col=1), value
            )
        outline = Outline()
        outline.group_rows(2, 3)
        outline.collapse(2, 3)
        scope = SubtotalScope(sheet=sheet)
        scope.hide_rows(sorted(outline.hidden_rows()))
        outcome = evaluate(
            parse_formula("=SUBTOTAL(9, B2:B5)"),
            sheet.value_of,
            scope.table(full_table),
        )
        assert outcome == 50.0
