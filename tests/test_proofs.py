from __future__ import annotations

from gridiron.cli import main
from gridiron.proofs import registry


class TestTheRegistry:
    def test_every_registered_proof_holds(self):
        assert registry.broken() == []

    def test_the_report_ends_with_the_tally(self):
        report = registry.report()
        assert report.splitlines()[-1].endswith("0 broken")


class TestTheCli:
    def test_summary_prints_the_one_line(self, capsys):
        assert main(["summary"]) == 0
        out = capsys.readouterr().out.strip()
        assert out.endswith("proofs (0 broken)")

    def test_check_exits_zero_while_everything_holds(self, capsys):
        assert main(["check"]) == 0
        assert "all proofs hold" in capsys.readouterr().out

    def test_proofs_lists_each_verdict(self, capsys):
        assert main(["proofs"]) == 0
        out = capsys.readouterr().out
        assert "sleepproof: holds:" in out
        assert "crosssheetproof: holds:" in out

    def test_no_command_prints_help(self, capsys):
        assert main([]) == 2
