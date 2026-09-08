"""Exporters: the grid leaves home in three costumes, none of them lying.

Export is where a spreadsheet's careful semantics usually
die: errors become empty strings, numbers become whatever
the template did, and the file that leaves the building
contradicts the sheet that stayed. These exporters carry the
value model out the door intact. An error exports as its
code, never as a blank, because a blank in a report is read
as zero and a #DIV/0! read as zero is the exact lie the
error existed to prevent. Markdown aligns numeric columns
right by inference over the body values, a column is numeric
when every filled cell in it is, and mixed columns stay
left, since alignment is a claim about a column's kind. HTML
escapes the three characters that break documents and tags
numeric cells with a class instead of inline styling,
leaving the look to whoever owns the stylesheet. The record
export keys each row by the header text and refuses
duplicate headers before writing anything, because two
columns with one name produce a dictionary that quietly ate
a column, and JSON output is the record list with keys in
header order, not alphabetized, since column order is part
of what the sheet said.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import Value, is_error, render


def _shown(value: Value) -> str:
    if value is None:
        return ""
    if is_error(value):
        return value.code
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        return render(value)
    return str(value)


@dataclass
class Exporter:
    sheet: Sheet
    region: RangeRef

    def _grid(self) -> list[list[Value]]:
        return [
            [
                self.sheet.value_of(
                    CellRef(row=row, col=col)
                )
                for col in range(
                    self.region.left, self.region.right + 1
                )
            ]
            for row in range(
                self.region.top, self.region.bottom + 1
            )
        ]

    def _headers(
        self, grid: list[list[Value]]
    ) -> list[str]:
        headers = [_shown(value) for value in grid[0]]
        if any(not header for header in headers):
            raise Invalid(
                "every exported column needs a header; "
                "an unlabeled column is a rumor in a report"
            )
        if len(set(headers)) != len(headers):
            raise Invalid(
                "duplicate headers would produce a "
                "dictionary that quietly ate a column"
            )
        return headers

    def _numeric_columns(
        self, grid: list[list[Value]]
    ) -> list[bool]:
        flags = []
        for col in range(len(grid[0])):
            filled = [
                row[col]
                for row in grid[1:]
                if row[col] is not None
            ]
            flags.append(
                bool(filled)
                and all(
                    isinstance(value, float)
                    and not isinstance(value, bool)
                    for value in filled
                )
            )
        return flags

    def to_markdown(self) -> str:
        grid = self._grid()
        headers = self._headers(grid)
        numeric = self._numeric_columns(grid)
        lines = ["| " + " | ".join(headers) + " |"]
        separators = [
            "---:" if numeric[index] else ":---"
            for index in range(len(headers))
        ]
        lines.append("| " + " | ".join(separators) + " |")
        for row in grid[1:]:
            cells = [_shown(value) for value in row]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join(lines)

    def to_html(self) -> str:
        grid = self._grid()
        headers = self._headers(grid)
        numeric = self._numeric_columns(grid)

        def escape(text: str) -> str:
            return (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

        lines = ["<table>", "  <thead>", "    <tr>"]
        for header in headers:
            lines.append(f"      <th>{escape(header)}</th>")
        lines.extend(["    </tr>", "  </thead>", "  <tbody>"])
        for row in grid[1:]:
            lines.append("    <tr>")
            for index, value in enumerate(row):
                shown = escape(_shown(value))
                if numeric[index]:
                    lines.append(
                        "      <td class=\"num\">"
                        f"{shown}</td>"
                    )
                else:
                    lines.append(f"      <td>{shown}</td>")
            lines.append("    </tr>")
        lines.extend(["  </tbody>", "</table>"])
        return "\n".join(lines)

    def to_records(self) -> list[dict[str, object]]:
        grid = self._grid()
        headers = self._headers(grid)
        records = []
        for row in grid[1:]:
            record: dict[str, object] = {}
            for header, value in zip(
                headers, row, strict=True
            ):
                if is_error(value):
                    record[header] = {"error": value.code}
                else:
                    record[header] = value
            records.append(record)
        return records

    def to_json(self) -> str:
        return json.dumps(self.to_records(), indent=2)
