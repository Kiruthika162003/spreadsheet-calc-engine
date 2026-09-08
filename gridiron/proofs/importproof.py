"""The import proof: the leading zero survives, and the two importers agree.

The number worth pinning is the leading zero. A ZIP code
07030 and a product code 00042 are text, not the numbers
7030 and 42, and an importer that helpfully parses them
loses the leading digit forever, which is the single most
common data-loss complaint in spreadsheet imports. The drill
imports a small CSV with a leading-zero field, a plain
number, a boolean, and text, and confirms the leading-zero
field arrives as text with its zero intact while the plain
number arrives as a number, both counted in the same
auditable report. The second half confirms the TSV importer
reads the identical inference ladder, so 00042 means the
same string through either door, because two importers that
disagree about what a field is are a bug waiting for the day
a file arrives in the other format. The last check is the
round trip: export the imported sheet back to CSV and the
leading zero is still quoted-or-bare correctly and reimports
to the same value, because an import that cannot survive its
own export is not a format, it is a one-way trip.
"""

from __future__ import annotations

from gridiron.csvio import export_csv, import_csv
from gridiron.importers import import_tsv
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef
from gridiron.sheet import Sheet

_CSV = "code,qty,flag,name\n00042,7,TRUE,Widget"
_TSV = "code\tqty\tflag\tname\n00042\t7\tTRUE\tWidget"


def run() -> Finding:
    csv_sheet = Sheet()
    csv_report = import_csv(csv_sheet, _CSV)
    code = csv_sheet.value_of(CellRef.parse("A2"))
    qty = csv_sheet.value_of(CellRef.parse("B2"))
    flag = csv_sheet.value_of(CellRef.parse("C2"))

    tsv_sheet = Sheet()
    import_tsv(tsv_sheet, _TSV)
    tsv_code = tsv_sheet.value_of(CellRef.parse("A2"))

    exported = export_csv(csv_sheet, 0, 0, 1, 3)
    reimported = Sheet()
    import_csv(reimported, exported)
    round_trip_code = reimported.value_of(
        CellRef.parse("A2")
    )

    numbers = {
        "code_is_text": code == "00042",
        "qty_is_number": qty == 7.0,
        "flag_is_bool": flag is True,
        "zeros_protected": csv_report.zeros_protected,
        "tsv_agrees": tsv_code == "00042",
        "round_trip_holds": round_trip_code == "00042",
    }
    holds = (
        numbers["code_is_text"]
        and numbers["qty_is_number"]
        and numbers["flag_is_bool"]
        and csv_report.zeros_protected == 1
        and numbers["tsv_agrees"]
        and numbers["round_trip_holds"]
    )
    return Finding(
        proof="importproof",
        claim=(
            "a leading-zero code imports as the text 00042 "
            "through both the CSV and TSV doors, counted as "
            "one protected field, and survives an export and "
            "reimport unchanged"
        ),
        numbers=numbers,
        holds=holds,
    )
