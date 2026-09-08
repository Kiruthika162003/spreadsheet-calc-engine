"""TSV and fixed-width import: the two formats that predate quoting.

Tab-separated text is the oldest interchange format that
still works, precisely because it never grew a quoting
grammar: a tab is a wall, a newline is a floor, and a field
simply may not contain either. This importer holds that line
honestly, a field is what sits between walls, and the type
inference is the csv module's stated ladder reused verbatim,
TRUE and FALSE become booleans, numbers become numbers
unless a leading zero marks them as identifiers, everything
else stays text, so the two importers cannot drift apart on
what 007 means. Fixed-width import reads the other ancient
format, columns defined by position, and the spec is
validated before a single character is read: columns must
not overlap, must not run backward, and must carry distinct
names, because a spec error repeated down ten thousand lines
is ten thousand errors with one cause. Short lines fill the
missing right-hand columns as empty, that is what a ragged
report edge means, but a line running past the last column
is refused with its line number, since trailing junk is
either a spec mistake or a data mistake and both deserve a
name, not a shrug.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.csvio import ImportReport, _infer
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def _place(
    sheet: Sheet,
    report: ImportReport,
    target: CellRef,
    raw: str,
) -> None:
    value = _infer(raw)
    if value is None:
        report.empties += 1
        return
    sheet.set_literal(target, value)
    if isinstance(value, bool):
        report.booleans += 1
    elif isinstance(value, float):
        report.numbers += 1
    else:
        report.texts += 1
        if raw.startswith("0") and len(raw) > 1:
            report.zeros_protected += 1


def import_tsv(
    sheet: Sheet, text: str, top: int = 0, left: int = 0
) -> ImportReport:
    report = ImportReport()
    for row_offset, line in enumerate(text.splitlines()):
        for col_offset, raw in enumerate(line.split("\t")):
            _place(
                sheet,
                report,
                CellRef(
                    row=top + row_offset,
                    col=left + col_offset,
                ),
                raw.strip(),
            )
    return report


@dataclass(frozen=True)
class FixedColumn:
    name: str
    start: int
    width: int


def _validate_spec(
    columns: tuple[FixedColumn, ...],
) -> None:
    if not columns:
        raise Invalid("a fixed-width spec needs columns")
    names = [column.name for column in columns]
    if len(set(names)) != len(names):
        raise Invalid(
            "the spec repeats a column name; ten thousand "
            "lines of one mistake still have one cause"
        )
    previous_end = -1
    for column in columns:
        if column.width < 1:
            raise Invalid(
                f"column {column.name} has width "
                f"{column.width}; a zero-width column "
                "reads nothing forever"
            )
        if column.start <= previous_end:
            raise Invalid(
                f"column {column.name} starts at "
                f"{column.start}, inside or before its "
                "neighbor; columns must not overlap or "
                "run backward"
            )
        previous_end = column.start + column.width - 1


def import_fixed(
    sheet: Sheet,
    text: str,
    columns: tuple[FixedColumn, ...],
    top: int = 0,
    left: int = 0,
) -> ImportReport:
    _validate_spec(columns)
    last = columns[-1]
    line_capacity = last.start + last.width
    report = ImportReport()
    for row_offset, line in enumerate(text.splitlines()):
        if len(line.rstrip()) > line_capacity:
            raise Invalid(
                f"line {row_offset + 1} runs past the last "
                "column; trailing junk is a spec mistake "
                "or a data mistake and both deserve a name"
            )
        for col_offset, column in enumerate(columns):
            raw = line[
                column.start : column.start + column.width
            ].strip()
            _place(
                sheet,
                report,
                CellRef(
                    row=top + row_offset,
                    col=left + col_offset,
                ),
                raw,
            )
    return report
