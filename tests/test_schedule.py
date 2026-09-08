from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.schedule import Scheduler, Task


def project() -> Scheduler:
    # A(3) -> C(2); B(2) -> C; C -> D(4). Critical: A,C,D=9.
    scheduler = Scheduler()
    scheduler.add(Task("A", 3.0))
    scheduler.add(Task("B", 2.0))
    scheduler.add(Task("C", 2.0, depends_on=("A", "B")))
    scheduler.add(Task("D", 4.0, depends_on=("C",)))
    return scheduler


class TestForwardPass:
    def test_a_task_starts_after_its_prerequisites(self):
        result = project().compute()
        assert result.earliest_start["A"] == 0.0
        assert result.earliest_start["C"] == 3.0
        assert result.earliest_start["D"] == 5.0

    def test_the_project_finishes_on_the_longest_path(self):
        assert project().compute().project_finish == 9.0

    def test_a_milestone_of_zero_duration(self):
        scheduler = Scheduler()
        scheduler.add(Task("start", 0.0))
        scheduler.add(
            Task("work", 5.0, depends_on=("start",))
        )
        result = scheduler.compute()
        assert result.earliest_finish["start"] == 0.0
        assert result.project_finish == 5.0


class TestCriticalPath:
    def test_the_zero_slack_tasks_are_critical(self):
        result = project().compute()
        assert result.critical_path() == ["A", "C", "D"]

    def test_the_slack_task_has_room(self):
        result = project().compute()
        # B (2) can start as late as 1 and still feed C at 3.
        assert result.slack["B"] == 1.0

    def test_two_critical_paths_are_both_reported(self):
        scheduler = Scheduler()
        scheduler.add(Task("A", 3.0))
        scheduler.add(Task("B", 3.0))
        scheduler.add(
            Task("end", 1.0, depends_on=("A", "B"))
        )
        result = scheduler.compute()
        assert result.critical_path() == ["A", "B", "end"]


class TestRefusals:
    def test_a_cycle_is_refused(self):
        scheduler = Scheduler()
        scheduler.add(Task("A", 1.0, depends_on=("B",)))
        scheduler.add(Task("B", 1.0, depends_on=("A",)))
        with pytest.raises(Invalid) as caught:
            scheduler.compute()
        assert "cycle" in str(caught.value)

    def test_an_unknown_prerequisite_is_refused(self):
        scheduler = Scheduler()
        scheduler.add(
            Task("A", 1.0, depends_on=("ghost",))
        )
        with pytest.raises(Invalid) as caught:
            scheduler.compute()
        assert "does not exist" in str(caught.value)

    def test_a_negative_duration_is_refused(self):
        scheduler = Scheduler()
        with pytest.raises(Invalid) as caught:
            scheduler.add(Task("A", -1.0))
        assert "backward" in str(caught.value)
