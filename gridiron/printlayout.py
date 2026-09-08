"""Print pagination: down then over, headers repeated, breaks obeyed.

Pagination is a tiling problem with three human rules laid
over it. Pages walk down the rows first and only then move
right to the next band of columns, the incumbent's order,
because a report is read down a column of pages and a
numbering that snakes across bands shuffles the story.
Header rows repeat at the top of every page, and the rent is
paid everywhere: the first page pays it because the header
physically sits there, later pages pay it for the reprint,
so every page's body capacity shrinks by the same amount, an
arithmetic the tests check rather than trust after the first
draft charged the first page nothing and overfilled it by
exactly one header. A header tall enough to eat the whole
page is refused by name since a report that is all header
and no body is stationery, and a cell inside the repeated
header has no single page to call home, which the page
lookup says instead of picking one. Manual
breaks are promises about meaning, quarter ends here, so a
break always starts a fresh page even when the automatic
tiling would not have, and a break pointed outside the print
region is refused as the typo it is. Every page can say
which cells it owns and every cell can say which page it
lands on, both directions, because the question during
review is always one of the two and rebuilding the tiling by
hand to answer it is how off-by-one-page errors ship.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef, index_to_column


@dataclass(frozen=True)
class Page:
    number: int
    top: int
    bottom: int
    left: int
    right: int
    repeated_header: bool

    def describe(self) -> str:
        rows = f"rows {self.top + 1}-{self.bottom + 1}"
        cols = (
            f"cols {index_to_column(self.left)}-"
            f"{index_to_column(self.right)}"
        )
        header = (
            " (+header)" if self.repeated_header else ""
        )
        return f"Page {self.number}: {rows}, {cols}{header}"

    def owns(self, ref: CellRef) -> bool:
        return (
            self.top <= ref.row <= self.bottom
            and self.left <= ref.col <= self.right
        )


@dataclass
class PrintPlanner:
    region: RangeRef
    rows_per_page: int
    cols_per_page: int
    header_rows: int = 0
    breaks: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.rows_per_page < 1 or self.cols_per_page < 1:
            raise Invalid(
                "a page needs at least one row and one "
                "column"
            )
        if self.header_rows >= self.rows_per_page:
            raise Invalid(
                f"{self.header_rows} header row(s) on a "
                f"{self.rows_per_page}-row page; the header "
                "ate the page and a report that is all "
                "header is stationery"
            )
        if self.header_rows < 0:
            raise Invalid("header rows cannot be negative")

    def add_break_before_row(self, row: int) -> str:
        if not (
            self.region.top < row <= self.region.bottom
        ):
            raise Invalid(
                f"a break before row {row + 1} falls "
                "outside the print region; a promise about "
                "meaning needs a place to stand"
            )
        self.breaks.add(row)
        return (
            f"break set before row {row + 1}; a fresh page "
            "starts there no matter what the tiling wanted"
        )

    def _row_bands(self) -> list[tuple[int, int, bool]]:
        bands: list[tuple[int, int, bool]] = []
        capacity = self.rows_per_page - self.header_rows
        first = True
        row = self.region.top + self.header_rows
        while row <= self.region.bottom:
            end = min(
                row + capacity - 1, self.region.bottom
            )
            for broken in sorted(self.breaks):
                if row < broken <= end:
                    end = broken - 1
                    break
            bands.append((row, end, not first))
            row = end + 1
            first = False
        return bands

    def _col_bands(self) -> list[tuple[int, int]]:
        bands = []
        col = self.region.left
        while col <= self.region.right:
            end = min(
                col + self.cols_per_page - 1,
                self.region.right,
            )
            bands.append((col, end))
            col = end + 1
        return bands

    def paginate(self) -> list[Page]:
        pages = []
        number = 1
        for left, right in self._col_bands():
            for top, bottom, repeated in self._row_bands():
                pages.append(
                    Page(
                        number=number,
                        top=top,
                        bottom=bottom,
                        left=left,
                        right=right,
                        repeated_header=repeated
                        and self.header_rows > 0,
                    )
                )
                number += 1
        return pages

    def page_of(self, ref: CellRef) -> int:
        header_bottom = (
            self.region.top + self.header_rows - 1
        )
        if (
            self.header_rows > 0
            and self.region.top <= ref.row <= header_bottom
            and self.region.left
            <= ref.col
            <= self.region.right
        ):
            raise Invalid(
                f"{ref.a1()} sits in the repeated header; "
                "it prints on every page and has no single "
                "home"
            )
        for page in self.paginate():
            if page.owns(ref):
                return page.number
        raise Invalid(
            f"{ref.a1()} lies outside the print region"
        )

    def plan(self) -> str:
        pages = self.paginate()
        lines = [page.describe() for page in pages]
        lines.append(
            f"{len(pages)} page(s), down then over"
        )
        return "\n".join(lines)
