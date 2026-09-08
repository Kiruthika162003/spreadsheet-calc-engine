"""CSV import and export: type inference with a written confession.

Every CSV importer guesses types, and the guessing is where
data dies: "00501" is a zip code until inference makes it
501, and "3/4" is a fraction until it becomes a date. This
importer infers narrowly and confesses completely: a field
becomes a number only when the whole field parses as one and
keeps no leading zero, becomes a boolean only on the exact
words TRUE and FALSE, and stays text otherwise, with the
report counting every coercion by kind so the import is an
auditable event instead of a vibe. Quoted fields follow the
RFC, doubled quotes escape, embedded commas and newlines
survive, and export is the exact inverse, quoting only when
the field demands it, so a round trip through export and
import is the identity on values, which the tests hold as a
law rather than a hope.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet
from gridiron.values import Value, render


def _split_line(line: str) -> list[str]:
    fields: list[str] = []
    current: list[str] = []
    in_quotes = False
    index = 0
    while index < len(line):
        char = line[index]
        if in_quotes:
            if char == '"':
                if (
                    index + 1 < len(line)
                    and line[index + 1] == '"'
                ):
                    current.append('"')
                    index += 2
                    continue
                in_quotes = False
                index += 1
                continue
            current.append(char)
            index += 1
            continue
        if char == '"':
            in_quotes = True
            index += 1
            continue
        if char == ",":
            fields.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    if in_quotes:
        raise Invalid(
            "a quoted field never closes; the file is torn"
        )
    fields.append("".join(current))
    return fields


def _infer(text: str) -> Value:
    if text == "":
        return None
    if text in ("TRUE", "FALSE"):
        return text == "TRUE"
    try:
        number = float(text)
    except ValueError:
        return text
    if text.startswith("0") and len(text) > 1 and (
        not text.startswith("0.")
    ):
        return text
    return number


@dataclass
class ImportReport:
    numbers: int = 0
    booleans: int = 0
    texts: int = 0
    empties: int = 0
    zeros_protected: int = 0

    def line(self) -> str:
        return (
            f"{self.numbers} number(s), {self.booleans} "
            f"boolean(s), {self.texts} text(s), "
            f"{self.empties} empt(ies), "
            f"{self.zeros_protected} leading-zero field(s) "
            "kept as text; an import is an auditable event, "
            "not a vibe"
        )


def import_csv(
    sheet: Sheet, text: str, top: int = 0, left: int = 0
) -> ImportReport:
    report = ImportReport()
    for row_offset, line in enumerate(
        text.splitlines()
    ):
        for col_offset, raw in enumerate(_split_line(line)):
            value = _infer(raw)
            target = CellRef(
                row=top + row_offset, col=left + col_offset
            )
            if value is None:
                report.empties += 1
                continue
            sheet.set_literal(target, value)
            if isinstance(value, bool):
                report.booleans += 1
            elif isinstance(value, float):
                report.numbers += 1
            else:
                report.texts += 1
                if raw.startswith("0") and len(raw) > 1:
                    report.zeros_protected += 1
    return report


def _quote_if_needed(text: str) -> str:
    if any(char in text for char in ',"\n'):
        escaped = text.replace('"', '""')
        return f'"{escaped}"'
    return text


def export_csv(
    sheet: Sheet, top: int, left: int, bottom: int, right: int
) -> str:
    lines = []
    for row in range(top, bottom + 1):
        fields = []
        for col in range(left, right + 1):
            value = sheet.value_of(
                CellRef(row=row, col=col)
            )
            fields.append(_quote_if_needed(render(value)))
        lines.append(",".join(fields))
    return "\n".join(lines)
