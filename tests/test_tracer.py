from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Missing
from gridiron.refs import CellRef
from gridiron.tracer import Tracer


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def model() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 10.0)
    engine.set_literal(ref("A2"), 20.0)
    engine.set_formula(ref("B1"), "=A1*2")
    engine.set_formula(ref("C1"), "=B1+A2")
    engine.set_formula(ref("D1"), "=SUM(A1:A9)")
    return engine


class TestPrecedents:
    def test_levels_walk_backward_through_the_model(self):
        trace = Tracer(engine=model()).precedents(ref("C1"))
        assert "level 1: A2, B1" in trace
        assert "level 2: A1" in trace

    def test_ranges_expand_only_to_occupied_cells(self):
        trace = Tracer(engine=model()).precedents(ref("D1"))
        assert "level 1: A1, A2" in trace
        assert "A3" not in trace

    def test_the_source_cell_says_so(self):
        trace = Tracer(engine=model()).precedents(ref("A1"))
        assert "nothing; it is a source" in trace

    def test_the_empty_cell_is_missing(self):
        with pytest.raises(Missing):
            Tracer(engine=model()).precedents(ref("Z9"))

    def test_cycles_are_marked_and_not_followed(self):
        engine = Engine()
        engine.set_formula(ref("A1"), "=B1+1")
        engine.set_formula(ref("B1"), "=A1+1")
        trace = Tracer(engine=engine).precedents(ref("A1"))
        assert "(cycle, not followed)" in trace


class TestDependents:
    def test_direct_feeds_are_listed(self):
        verdict = Tracer(engine=model()).dependents(ref("B1"))
        assert verdict.startswith("B1 feeds C1")

    def test_the_range_watcher_is_the_classic_blind_spot(self):
        verdict = Tracer(engine=model()).dependents(ref("A2"))
        assert "C1" in verdict
        assert "D1 watch(es) through a range" in verdict
        assert "classic blind spot" in verdict

    def test_the_unwatched_cell_is_safe_to_delete(self):
        verdict = Tracer(engine=model()).dependents(ref("Z9"))
        assert "deleting it breaks no formula" in verdict
