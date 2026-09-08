from __future__ import annotations

import pytest

from gridiron.engine import Engine
from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef
from gridiron.snapshots import SnapshotVault


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def working_engine() -> Engine:
    engine = Engine()
    engine.set_literal(ref("A1"), 100.0)
    engine.set_literal(ref("A2"), 50.0)
    engine.set_formula(ref("B1"), "=A1+A2")
    return engine


class TestTaking:
    def test_a_snapshot_counts_its_cells(self):
        vault = SnapshotVault(sheet=working_engine().sheet)
        assert "3 cell(s)" in vault.take("before-close")

    def test_one_name_one_moment(self):
        vault = SnapshotVault(sheet=working_engine().sheet)
        vault.take("tuesday")
        with pytest.raises(Invalid) as caught:
            vault.take("tuesday")
        assert "which-tuesday" in str(caught.value)

    def test_the_catalog_lists_by_name(self):
        vault = SnapshotVault(sheet=working_engine().sheet)
        vault.take("b")
        vault.take("a")
        assert vault.catalog().splitlines() == [
            "a: 3 cell(s)",
            "b: 3 cell(s)",
        ]


class TestDiffing:
    def test_the_three_verbs_count_separately(self):
        engine = working_engine()
        vault = SnapshotVault(sheet=engine.sheet)
        vault.take("before")
        engine.set_literal(ref("A1"), 150.0)
        engine.set_literal(ref("C1"), 7.0)
        engine.clear(ref("A2"))
        report = vault.diff("before")
        assert report.line() == (
            "1 added, 1 removed, 1 changed, 1 untouched"
        )
        assert report.changed == ["A1: 100 -> 150"]
        assert report.added == ["C1 = 7"]
        assert report.removed == ["A2 was 50"]

    def test_a_formula_text_change_is_a_change(self):
        engine = working_engine()
        vault = SnapshotVault(sheet=engine.sheet)
        vault.take("before")
        engine.set_formula(ref("B1"), "=A2+A1")
        report = vault.diff("before")
        assert report.changed == ["B1: =A1+A2 -> =A2+A1"]

    def test_an_untouched_sheet_diffs_clean(self):
        vault = SnapshotVault(sheet=working_engine().sheet)
        vault.take("before")
        report = vault.diff("before")
        assert report.line() == (
            "0 added, 0 removed, 0 changed, 3 untouched"
        )


class TestRestore:
    def test_the_round_trip_and_the_recalc_sentence(self):
        engine = working_engine()
        vault = SnapshotVault(sheet=engine.sheet)
        vault.take("golden")
        engine.set_literal(ref("A1"), 999.0)
        engine.set_formula(ref("B1"), "=A1*2")
        verdict = vault.restore("golden")
        assert "recalculate before trusting" in verdict
        engine.full_recalc()
        assert engine.value(ref("A1")) == 100.0
        assert engine.value(ref("B1")) == 150.0

    def test_restore_removes_cells_born_after(self):
        engine = working_engine()
        vault = SnapshotVault(sheet=engine.sheet)
        vault.take("golden")
        engine.set_literal(ref("Z9"), 1.0)
        vault.restore("golden")
        assert engine.sheet.value_of(ref("Z9")) is None

    def test_restoring_a_ghost_is_missing_not_a_noop(self):
        vault = SnapshotVault(sheet=working_engine().sheet)
        vault.take("only-one")
        with pytest.raises(Missing) as caught:
            vault.restore("never-taken")
        assert "taken: only-one" in str(caught.value)

    def test_dropping_forgets_the_name(self):
        vault = SnapshotVault(sheet=working_engine().sheet)
        vault.take("tmp")
        assert "dropped" in vault.drop("tmp")
        assert vault.catalog() == "no snapshots taken"
