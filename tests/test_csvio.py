from __future__ import annotations

import pytest

from gridiron.csvio import export_csv, import_csv
from gridiron.errors import Invalid
from gridiron.refs import CellRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


CSV = (
    'item,count,active,zip\n'
    'apples,40,TRUE,00501\n'
    '"bread, rye",15,FALSE,10001\n'
)


class TestImport:
    def test_narrow_inference_with_a_confession(self):
        sheet = Sheet()
        report = import_csv(sheet, CSV)
        assert sheet.value_of(ref("B2")) == 40.0
        assert sheet.value_of(ref("C2")) is True
        assert sheet.value_of(ref("A3")) == "bread, rye"
        assert report.numbers == 3
        assert report.booleans == 2

    def test_the_zip_code_survives_inference(self):
        sheet = Sheet()
        report = import_csv(sheet, CSV)
        assert sheet.value_of(ref("D2")) == "00501"
        assert report.zeros_protected == 1
        assert "auditable event, not a vibe" in report.line()

    def test_decimals_under_one_still_become_numbers(self):
        sheet = Sheet()
        import_csv(sheet, "0.5")
        assert sheet.value_of(ref("A1")) == 0.5

    def test_empty_fields_stay_absent(self):
        sheet = Sheet()
        report = import_csv(sheet, "a,,c")
        assert sheet.value_of(ref("B1")) is None
        assert report.empties == 1

    def test_the_torn_file_is_named(self):
        with pytest.raises(Invalid) as caught:
            import_csv(Sheet(), '"unclosed')
        assert "the file is torn" in str(caught.value)


class TestExportAndTheLaw:
    def test_export_quotes_only_when_demanded(self):
        sheet = Sheet()
        import_csv(sheet, CSV)
        out = export_csv(sheet, 0, 0, 2, 3)
        assert '"bread, rye"' in out
        assert '"apples"' not in out

    def test_the_round_trip_is_the_identity_on_values(self):
        first = Sheet()
        import_csv(first, CSV)
        exported = export_csv(first, 0, 0, 2, 3)
        second = Sheet()
        import_csv(second, exported)
        for key in first.cells:
            row, col = key
            assert second.value_of(
                CellRef(row=row, col=col)
            ) == first.value_of(CellRef(row=row, col=col))
