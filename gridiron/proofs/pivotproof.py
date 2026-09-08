"""The pivot proof: the grand average weighs records, not buckets.

The one number this proof exists to pin is the difference
between the grand average and the average of the row
averages, because that difference is where pivot tables
quietly lie. The drill builds a two-region table, three East
records and one West, aggregates the value column by region
as an average, and computes both quantities: the grand
average over all four records, and the mean of the two row
averages. They must differ, and the grand must be the
record-weighted one, because the mean of means weights a
three-record bucket the same as a one-record bucket and that
lie has misread a thousand quarterly reviews. The second
half drills error poisoning: a #DIV/0! planted in one East
record must wreck the East bucket, the East row total, and
the grand total while the West bucket stands untouched,
which is the value model's promise that errors flow but do
not explode, carried intact through the group-by.
"""

from __future__ import annotations

from gridiron.pivot import PivotSpec, PivotTable
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet
from gridiron.values import ErrorValue, is_error

ROWS = (
    ("Region", "Sales"),
    ("East", 100.0),
    ("East", 200.0),
    ("East", 300.0),
    ("West", 40.0),
)


def _sheet() -> Sheet:
    sheet = Sheet()
    for row_index, row in enumerate(ROWS):
        for col_index, value in enumerate(row):
            sheet.set_literal(
                CellRef(row=row_index, col=col_index), value
            )
    return sheet


def _table(sheet: Sheet, agg: str) -> PivotTable:
    return PivotTable(
        sheet=sheet,
        region=RangeRef.parse("A1:B5"),
        spec=PivotSpec(
            rows="Region", values="Sales", agg=agg
        ),
    )


def run() -> Finding:
    sheet = _sheet()
    report = _table(sheet, "AVERAGE").build()
    east = report.row_totals["East"]
    west = report.row_totals["West"]
    grand = report.grand
    mean_of_means = (east + west) / 2

    poisoned_sheet = _sheet()
    poisoned_sheet.set_literal(
        CellRef.parse("B2"),
        ErrorValue(code="#DIV/0!", note="planted"),
    )
    poisoned = _table(poisoned_sheet, "SUM").build()

    numbers = {
        "east_average": east,
        "west_average": west,
        "grand_average": grand,
        "mean_of_means": mean_of_means,
        "grand_weighs_records": grand == 160.0
        and grand != mean_of_means,
        "east_bucket_poisoned": is_error(
            poisoned.row_totals["East"]
        ),
        "grand_poisoned": is_error(poisoned.grand),
        "west_bucket_survived": poisoned.row_totals["West"]
        == 40.0,
    }
    holds = (
        east == 200.0
        and west == 40.0
        and numbers["grand_weighs_records"]
        and numbers["east_bucket_poisoned"]
        and numbers["grand_poisoned"]
        and numbers["west_bucket_survived"]
    )
    return Finding(
        proof="pivotproof",
        claim=(
            "the grand average is the record-weighted 160, "
            "not the 120 the mean of row averages would "
            "give, and a planted error wrecks only the "
            "buckets that contain it"
        ),
        numbers=numbers,
        holds=holds,
    )
