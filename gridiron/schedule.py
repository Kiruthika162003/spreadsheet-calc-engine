"""Scheduling: earliest start and finish, and the path that owns the deadline.

A project schedule is a dependency graph with durations, and
the two questions it answers are when can each task start and
which tasks, if they slip, slip the whole project. This
module computes the forward pass, each task starts when its
latest prerequisite finishes, and then the backward pass,
each task's latest allowable finish without delaying the
project, and the tasks whose slack is zero are the critical
path. The forward pass is a topological walk, and a cycle in
the dependencies is refused by name rather than looping
forever, because a task that depends on itself through a
chain is a planning error, not a schedule, and the honest
response is to point at the cycle. A dependency on a task
that does not exist is refused too, with the missing name
quoted, because a schedule silently ignoring an unknown
prerequisite computes a start date earlier than reality and
that optimism ships as a missed deadline. Slack is the
difference between the latest and earliest start, and the
critical path is not necessarily unique, so the module
reports every zero-slack task rather than one arbitrary
chain, because telling a manager one critical path when two
exist hides half the risk. Durations are non-negative, a
zero-duration milestone being legitimate, and a negative one
refused as the data-entry slip it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid


@dataclass(frozen=True)
class Task:
    name: str
    duration: float
    depends_on: tuple[str, ...] = ()


@dataclass
class ScheduleResult:
    earliest_start: dict[str, float]
    earliest_finish: dict[str, float]
    latest_start: dict[str, float]
    slack: dict[str, float]
    project_finish: float

    def critical_path(self) -> list[str]:
        return sorted(
            name
            for name, slack in self.slack.items()
            if abs(slack) < 1e-9
        )


@dataclass
class Scheduler:
    tasks: dict[str, Task] = field(default_factory=dict)

    def add(self, task: Task) -> None:
        if task.duration < 0:
            raise Invalid(
                f"task {task.name!r} has a negative "
                "duration; a milestone may be zero but time "
                "does not run backward"
            )
        self.tasks[task.name] = task

    def _order(self) -> list[str]:
        state: dict[str, int] = {}
        order: list[str] = []

        def visit(name: str, trail: tuple[str, ...]) -> None:
            if name not in self.tasks:
                raise Invalid(
                    f"task {trail[-1]!r} depends on "
                    f"{name!r}, which does not exist; an "
                    "unknown prerequisite ships as a missed "
                    "deadline"
                )
            if state.get(name) == 2:
                return
            if state.get(name) == 1:
                loop = " -> ".join([*trail, name])
                raise Invalid(
                    f"the dependencies cycle: {loop}; a task "
                    "that depends on itself is a planning "
                    "error, not a schedule"
                )
            state[name] = 1
            for prerequisite in self.tasks[name].depends_on:
                visit(prerequisite, (*trail, name))
            state[name] = 2
            order.append(name)

        for name in self.tasks:
            visit(name, ())
        return order

    def compute(self) -> ScheduleResult:
        order = self._order()
        earliest_start: dict[str, float] = {}
        earliest_finish: dict[str, float] = {}
        for name in order:
            task = self.tasks[name]
            start = max(
                (
                    earliest_finish[dep]
                    for dep in task.depends_on
                ),
                default=0.0,
            )
            earliest_start[name] = start
            earliest_finish[name] = start + task.duration
        project_finish = max(
            earliest_finish.values(), default=0.0
        )
        latest_finish: dict[str, float] = dict.fromkeys(self.tasks, project_finish)
        dependents: dict[str, list[str]] = {
            name: [] for name in self.tasks
        }
        for name in self.tasks:
            for dep in self.tasks[name].depends_on:
                dependents[dep].append(name)
        for name in reversed(order):
            successors = dependents[name]
            if successors:
                latest_finish[name] = min(
                    latest_finish[s]
                    - self.tasks[s].duration
                    for s in successors
                )
        latest_start = {
            name: latest_finish[name]
            - self.tasks[name].duration
            for name in self.tasks
        }
        slack = {
            name: latest_start[name]
            - earliest_start[name]
            for name in self.tasks
        }
        return ScheduleResult(
            earliest_start=earliest_start,
            earliest_finish=earliest_finish,
            latest_start=latest_start,
            slack=slack,
            project_finish=project_finish,
        )
