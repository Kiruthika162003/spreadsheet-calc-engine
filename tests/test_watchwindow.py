from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.watchwindow import WatchWindow


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def wired() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 10.0)
    engine.set_formula(ref("B1"), "=A1*2")
    engine.set_formula(ref("C1"), "=B1+1")
    return engine


class TestPolling:
    def test_a_fresh_watch_reads_unchanged(self):
        window = WatchWindow(engine=wired())
        window.add(ref("B1"))
        assert window.poll() == []

    def test_an_edit_upstream_is_reported(self):
        engine = wired()
        window = WatchWindow(engine=engine)
        window.add(ref("B1"))
        window.add(ref("C1"))
        engine.set_literal(ref("A1"), 100.0)
        changes = window.poll()
        assert "B1: 20 -> 200" in changes
        assert "C1: 21 -> 201" in changes

    def test_a_second_poll_is_quiet(self):
        engine = wired()
        window = WatchWindow(engine=engine)
        window.add(ref("B1"))
        engine.set_literal(ref("A1"), 100.0)
        window.poll()
        assert window.poll() == []

    def test_the_report_names_the_quiet(self):
        window = WatchWindow(engine=wired())
        window.add(ref("A1"))
        assert window.report() == "1 watched, none changed"


class TestErrorsAndGaps:
    def test_a_cell_becoming_an_error_is_a_change(self):
        engine = wired()
        window = WatchWindow(engine=engine)
        window.add(ref("B1"))
        engine.set_formula(ref("B1"), "=A1/0")
        changes = window.poll()
        assert "B1: 20 -> #DIV/0!" in changes

    def test_readding_takes_a_fresh_snapshot(self):
        engine = wired()
        window = WatchWindow(engine=engine)
        window.add(ref("B1"))
        window.remove(ref("B1"))
        engine.set_literal(ref("A1"), 100.0)
        window.add(ref("B1"))
        # The change happened while not watching; the fresh
        # snapshot must not report it.
        assert window.poll() == []


class TestRefusals:
    def test_double_watching_is_refused(self):
        window = WatchWindow(engine=wired())
        window.add(ref("A1"))
        with pytest.raises(Invalid):
            window.add(ref("A1"))

    def test_removing_an_unwatched_cell_is_refused(self):
        window = WatchWindow(engine=wired())
        with pytest.raises(Invalid):
            window.remove(ref("Z9"))
