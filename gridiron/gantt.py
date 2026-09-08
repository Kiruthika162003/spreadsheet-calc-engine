"""Gantt rendering: a schedule drawn as bars on a shared time axis.

A schedule is numbers until someone draws it, and the drawing
is where a mistake becomes visible: a bar that starts before
its prerequisite finishes is a scheduling error the eye
catches instantly and a table hides. This renderer takes a
computed schedule and lays each task on one row of a shared
time axis, the bar spanning its earliest start to its
earliest finish, so two bars that should not overlap visibly
do or do not. Critical-path tasks are drawn with a different
fill than tasks with slack, because the whole point of the
critical path is to see it, and a chart that drew every task
the same would bury the one insight the schedule computed.
Slack is drawn as a trailing marker showing how far a task
could slip before it becomes critical, so a reader sees not
just what is tight but how much room the loose tasks have. A
zero-duration milestone is drawn as a single marker rather
than an empty bar, because a milestone is a moment not a
span and an empty bar reads as missing data. The axis scales
to the project finish so the whole plan fits one width, and
the renderer refuses a width too small to distinguish the
tasks rather than drawing bars that all collapse to one
column and lie about being simultaneous.
"""

from __future__ import annotations

from gridiron.errors import Invalid
from gridiron.schedule import Scheduler, ScheduleResult


def render_gantt(
    scheduler: Scheduler, width: int = 40
) -> str:
    result = scheduler.compute()
    return render_result(scheduler, result, width)


def render_result(
    scheduler: Scheduler,
    result: ScheduleResult,
    width: int = 40,
) -> str:
    finish = result.project_finish
    if finish <= 0:
        raise Invalid(
            "the project has no duration to chart"
        )
    if width < 4:
        raise Invalid(
            "a chart narrower than four columns collapses "
            "the tasks into a lie about simultaneity"
        )
    critical = set(result.critical_path())
    names = sorted(
        scheduler.tasks,
        key=lambda n: (
            result.earliest_start[n],
            n,
        ),
    )
    label_width = max(len(n) for n in names)
    lines = []
    for name in names:
        start = result.earliest_start[name]
        end = result.earliest_finish[name]
        start_col = round(start / finish * width)
        end_col = round(end / finish * width)
        slack = result.slack[name]
        slack_cols = round(slack / finish * width)
        fill = "#" if name in critical else "="
        if end_col == start_col:
            bar = " " * start_col + "*"
        else:
            bar = (
                " " * start_col
                + fill * (end_col - start_col)
            )
        bar += "." * slack_cols
        tag = " (critical)" if name in critical else ""
        lines.append(
            f"{name.ljust(label_width)} |{bar}{tag}"
        )
    lines.append(
        f"{'finish'.ljust(label_width)} | {finish:g} "
        "time unit(s)"
    )
    return "\n".join(lines)
