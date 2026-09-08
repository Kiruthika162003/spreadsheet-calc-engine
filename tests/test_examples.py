from __future__ import annotations

from examples import firstsheet


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
