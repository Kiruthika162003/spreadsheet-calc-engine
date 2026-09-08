from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.gantt import render_gantt
from gridiron.schedule import Scheduler, Task


def project() -> Scheduler:
    scheduler = Scheduler()
    scheduler.add(Task("A", 3.0))
    scheduler.add(Task("B", 2.0))
    scheduler.add(Task("C", 2.0, depends_on=("A", "B")))
    scheduler.add(Task("D", 4.0, depends_on=("C",)))
    return scheduler


class TestRendering:
    def test_the_lines_read_as_a_chart(self):
        chart = render_gantt(project(), width=18)
        lines = chart.splitlines()
        assert lines[0].startswith("A |")
        assert lines[-1].startswith("finish")
        assert "9 time unit(s)" in lines[-1]

    def test_critical_tasks_are_marked(self):
        chart = render_gantt(project(), width=18)
        assert "A |###### (critical)" in chart
        assert "(critical)" in chart

    def test_slack_tasks_use_a_different_fill(self):
        chart = render_gantt(project(), width=18)
        b_line = next(
            line
            for line in chart.splitlines()
            if line.startswith("B ")
        )
        assert "=" in b_line
        assert "(critical)" not in b_line
        # B has 2 units of slack, drawn as trailing dots.
        assert "." in b_line

    def test_tasks_sort_by_start_then_name(self):
        chart = render_gantt(project(), width=18)
        order = [
            line[0]
            for line in chart.splitlines()
            if line[0] in "ABCD"
        ]
        assert order == ["A", "B", "C", "D"]


class TestMilestones:
    def test_a_zero_duration_task_is_a_marker(self):
        scheduler = Scheduler()
        scheduler.add(Task("kickoff", 0.0))
        scheduler.add(
            Task("work", 5.0, depends_on=("kickoff",))
        )
        chart = render_gantt(scheduler, width=10)
        kickoff = next(
            line
            for line in chart.splitlines()
            if line.startswith("kickoff")
        )
        assert "*" in kickoff


class TestRefusals:
    def test_a_zero_duration_project_is_refused(self):
        scheduler = Scheduler()
        scheduler.add(Task("only", 0.0))
        with pytest.raises(Invalid) as caught:
            render_gantt(scheduler)
        assert "no duration to chart" in str(caught.value)

    def test_too_narrow_a_chart_is_refused(self):
        with pytest.raises(Invalid) as caught:
            render_gantt(project(), width=2)
        assert "simultaneity" in str(caught.value)
