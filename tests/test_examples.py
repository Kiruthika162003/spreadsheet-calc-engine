from __future__ import annotations

from examples import (
    auditday,
    budgetsheet,
    firstsheet,
    quarterclose,
    sciencelab,
    spillsheet,
    undosession,
    workbooktour,
)


class TestFirstSheet:
    def test_the_ledger_reads_end_to_end(self, capsys):
        assert firstsheet.main() == 0
        out = capsys.readouterr().out
        assert "total:   295.12" in out
        assert "average: 82.7" in out
        assert (
            "edit:    A2 becomes 100; 3 evaluated, "
            "2 formula(s) slept"
        ) in out
        assert "total:   312.97" in out
        assert "label:   Q1" in out
        assert "seek:    solved: A3 = 74.12109375" in out


class TestBudgetSheet:
    def test_the_budget_reads_end_to_end(self, capsys):
        assert budgetsheet.main() == 0
        out = capsys.readouterr().out
        assert "import:  5 number(s), 0 boolean(s), 7 text(s)" in out
        assert "total:   2030" in out
        assert "rent:    1280" in out
        assert "food:    2 line items" in out
        assert "verdict: rent heavy" in out
        assert "the classic blind spot" in out


class TestQuarterClose:
    def test_the_close_reads_end_to_end(self, capsys):
        assert quarterclose.main() == 0
        out = capsys.readouterr().out
        assert "workdays: 65 in the quarter" in out
        assert "net:      73,912.50" in out
        assert "filed: C1=73912.5" in out
        assert "audited: C1=77420" in out


class TestWorkbookTour:
    def test_the_tour_reads_end_to_end(self, capsys):
        assert workbooktour.main() == 0
        out = capsys.readouterr().out
        assert "margin:  1780" in out
        assert "share:   0.445" in out
        assert (
            "1 cross-sheet formula(s) refreshed in "
            "2 round(s)"
        ) in out
        assert "margin:  1480" in out
        assert "Revenue dropped; 2 formula(s)" in out
        assert "wound:   C1 now reads #REF!" in out


class TestScienceLab:
    def test_the_lab_reads_end_to_end(self, capsys):
        assert sciencelab.main() == 0
        out = capsys.readouterr().out
        assert "mean:    5.13" in out
        assert "median:  5" in out
        assert "stdev:   0.4218" in out
        assert "p90:     5.65" in out
        assert "bins:    4x1 grid spilled from E1" in out
        assert "counts:  4 3 1 2" in out
        assert "trend:   Reading: [ :.=. -#..]" in out
        assert "4.7 to 6.1" in out


class TestAuditDay:
    def test_the_audit_reads_end_to_end(self, capsys):
        assert auditday.main() == 0
        out = capsys.readouterr().out
        assert "census:  #DIV/0!: 1 born, 2 echo(es)" in out
        assert "origin:  B2" in out
        assert "trail:   D1 <- C1 <- B2" in out
        assert "wall:    load-bearing wall: B1" in out
        assert "spread:  B1 feeds B2, C1" in out
        assert "healed:  D1 is healthy" in out
        assert "result:  D1 = 2640" in out


class TestUndoSession:
    def test_the_session_reads_end_to_end(self, capsys):
        assert undosession.main() == 0
        out = capsys.readouterr().out
        assert "snapshot 'baseline' holds 3 cell(s)" in out
        assert (
            "pending: 1 edit(s) deferred; 2 formula(s) stale"
        ) in out
        assert "settled: C1 = 440" in out
        assert "typo:    C1 = 2197.8" in out
        assert "undo:    undid the edit at A1" in out
        assert "back:    C1 = 440" in out
        assert "0 added, 0 removed, 1 changed" in out
        assert "restored: C1 = 220" in out


class TestSpillSheet:
    def test_the_spill_sheet_reads_end_to_end(self, capsys):
        assert spillsheet.main() == 0
        out = capsys.readouterr().out
        assert "transpose: 2x3 grid spilled from E1" in out
        assert "row1:      Ada Grace Alan" in out
        assert "filter:    2x2 grid spilled from E5" in out
        assert "kept:      Ada, Alan" in out
        assert "sortby:    3x1 grid spilled from G5" in out
        assert "ranked:    Alan, Ada, Grace" in out
