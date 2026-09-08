from __future__ import annotations

import pytest

from gridiron.dotgraph import dot_graph
from gridiron.engine import Engine
from gridiron.errors import Missing
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def plumbing() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 10.0)
    engine.set_literal(ref("A2"), 20.0)
    engine.set_literal(ref("A3"), 30.0)
    engine.set_formula(ref("B1"), "=A1*2")
    engine.set_formula(ref("C1"), "=SUM(A1:A3)")
    engine.set_formula(ref("D1"), "=B1+C1")
    return engine


class TestTheDrawing:
    def test_the_header_and_the_closer(self):
        text = dot_graph(plumbing())
        lines = text.splitlines()
        assert lines[0] == "digraph workbook {"
        assert lines[-1] == "}"

    def test_formulas_show_their_text(self):
        text = dot_graph(plumbing())
        assert '"B1" [label="B1\\n=A1*2"];' in text
        assert '"A1" [label="A1\\n10"];' in text

    def test_ranges_are_one_node_not_a_hairball(self):
        text = dot_graph(plumbing())
        assert '"A1:A3" [shape=box3d];' in text
        assert '"A1:A3" -> "C1";' in text
        assert '"A2" -> "C1";' not in text

    def test_edges_are_sorted_for_stable_diffs(self):
        text = dot_graph(plumbing())
        edge_lines = [
            line
            for line in text.splitlines()
            if "->" in line
        ]
        assert edge_lines == sorted(edge_lines)

    def test_a_wound_is_filled_in_the_picture(self):
        engine = plumbing()
        engine.set_formula(ref("B1"), "=A1/0")
        text = dot_graph(engine)
        assert "fillcolor=lightpink" in text
        assert '"B1" [label="B1\\n=A1/0" ' in text


class TestFocus:
    def test_the_cone_keeps_ancestors_and_descendants(self):
        engine = plumbing()
        engine.set_formula(ref("Z9"), "=A2*5")
        text = dot_graph(engine, focus=ref("B1"))
        assert '"B1"' in text
        assert '"D1"' in text
        assert '"Z9"' not in text

    def test_an_unknown_focus_is_refused(self):
        with pytest.raises(Missing) as caught:
            dot_graph(plumbing(), focus=ref("Q7"))
        assert "empty page is not a drawing" in str(
            caught.value
        )
