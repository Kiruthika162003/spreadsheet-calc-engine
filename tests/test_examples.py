from __future__ import annotations

from examples import budgetsheet, firstsheet, quarterclose


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
