from __future__ import annotations

import pytest

from gridiron.dedup import Deduplicator
from gridiron.errors import Invalid
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def table(rows: list[tuple]) -> Sheet:
    sheet = Sheet()
    for row_index, row in enumerate(rows):
        for col_index, value in enumerate(row):
            if value is not None:
                sheet.set_literal(
                    CellRef(row=row_index, col=col_index),
                    value,
                )
    return sheet


def region(rows: int, cols: int) -> RangeRef:
    return RangeRef(
        top=0, left=0, bottom=rows - 1, right=cols - 1
    )


class TestFirstSightingWins:
    def test_duplicates_collapse_to_the_first(self):
        sheet = table(
            [
                ("Ada", 1.0),
                ("Grace", 2.0),
                ("Ada", 3.0),
                ("Grace", 4.0),
            ]
        )
        report = Deduplicator(sheet=sheet).dedup(
            region(4, 2), key_cols=(0,)
        )
        assert report.kept == 2
        assert sheet.value_of(ref("A1")) == "Ada"
        assert sheet.value_of(ref("B1")) == 1.0
        assert sheet.value_of(ref("A2")) == "Grace"
        assert sheet.value_of(ref("A3")) is None

    def test_the_report_names_what_it_dropped(self):
        sheet = table([("x",), ("x",), ("y",)])
        report = Deduplicator(sheet=sheet).dedup(
            region(3, 1), key_cols=(0,)
        )
        assert report.dropped == [("2", "row 1")]
        assert "1 duplicate(s) removed" in report.line()


class TestKeyIdentity:
    def test_number_and_text_five_differ(self):
        sheet = table([(5.0,), ("5",)])
        report = Deduplicator(sheet=sheet).dedup(
            region(2, 1), key_cols=(0,)
        )
        assert report.kept == 2

    def test_blank_is_a_key_not_a_wildcard(self):
        sheet = table([(None,), (None,), ("x",)])
        report = Deduplicator(sheet=sheet).dedup(
            region(3, 1), key_cols=(0,)
        )
        assert report.kept == 2

    def test_a_multi_column_key(self):
        sheet = table(
            [
                ("Ada", "Eng"),
                ("Ada", "Ops"),
                ("Ada", "Eng"),
            ]
        )
        report = Deduplicator(sheet=sheet).dedup(
            region(3, 2), key_cols=(0, 1)
        )
        assert report.kept == 2


class TestCaseFolding:
    def test_off_by_default(self):
        sheet = table([("Ada",), ("ADA",)])
        report = Deduplicator(sheet=sheet).dedup(
            region(2, 1), key_cols=(0,)
        )
        assert report.kept == 2

    def test_on_when_asked(self):
        sheet = table([("Ada",), ("ADA",)])
        report = Deduplicator(sheet=sheet).dedup(
            region(2, 1), key_cols=(0,), fold_case=True
        )
        assert report.kept == 1


class TestRefusals:
    def test_a_formula_key_is_refused(self):
        sheet = table([("a",), ("b",)])
        sheet.set_formula(ref("A2"), "=1+1")
        with pytest.raises(Invalid) as caught:
            Deduplicator(sheet=sheet).dedup(
                region(2, 1), key_cols=(0,)
            )
        assert "moving target" in str(caught.value)

    def test_a_key_column_outside_the_region(self):
        sheet = table([("a",)])
        with pytest.raises(Invalid) as caught:
            Deduplicator(sheet=sheet).dedup(
                region(1, 1), key_cols=(5,)
            )
        assert "outside" in str(caught.value)
