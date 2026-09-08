from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.history import HistoryLedger
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def ledger() -> HistoryLedger:
    built = HistoryLedger(sheet=Sheet())
    built.record_literal("asha", ref("B7"), 0.19)
    built.record_formula("ben", ref("C1"), "=B7*100")
    built.record_literal("asha", ref("B7"), 0.21)
    return built


class TestBlame:
    def test_the_sentence_has_a_defendant(self):
        verdict = ledger().blame(ref("B7"))
        assert verdict.startswith(
            "B7: last touched by asha at edit 3, 0.19 to 0.21"
        )
        assert "a sentence with a defendant" in verdict

    def test_the_untouched_cell_is_reassuring(self):
        verdict = ledger().blame(ref("Z9"))
        assert "nobody ever touched it" in verdict
        assert "most reassuring sentence" in verdict

    def test_the_first_edit_shows_the_empty_before(self):
        built = HistoryLedger(sheet=Sheet())
        built.record_literal("asha", ref("A1"), 5.0)
        assert "(empty) to 5" in built.blame(ref("A1"))


class TestTheDiff:
    def test_the_reviewers_view_reconstructs(self):
        diff = ledger().diff_since(1)
        assert diff.startswith("2 edit(s) since 1:")
        assert "2. ben: C1 (empty) to =B7*100" in diff
        assert "3. asha: B7 0.19 to 0.21" in diff

    def test_the_quiet_interval_says_so(self):
        assert ledger().diff_since(99) == (
            "nothing changed since edit 99"
        )


class TestDiscipline:
    def test_authorless_edits_wait(self):
        built = HistoryLedger(sheet=Sheet())
        with pytest.raises(Invalid) as caught:
            built.record_literal(" ", ref("A1"), 1.0)
        assert "carry an author or they wait" in str(
            caught.value
        )

    def test_the_ledger_still_writes_the_sheet(self):
        built = ledger()
        assert built.sheet.value_of(ref("B7")) == 0.21
