from __future__ import annotations

import pytest

from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef
from gridiron.workbook import Workbook


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


def book() -> Workbook:
    built = Workbook()
    data = built.add_sheet("Data")
    data.set_literal(ref("A1"), 42.0)
    summary = built.add_sheet("Summary")
    summary.set_formula(ref("B1"), "=1+1")
    return built


class TestNaming:
    def test_lookup_folds_case_and_display_preserves_it(self):
        built = book()
        assert built.sheet("DATA") is built.sheet("data")
        assert built.display_names["data"] == "Data"

    def test_case_differences_do_not_make_two_sheets(self):
        built = book()
        with pytest.raises(Invalid) as caught:
            built.add_sheet("DATA")
        assert "case differences do not make two" in str(
            caught.value
        )

    def test_the_separator_is_reserved(self):
        with pytest.raises(Invalid):
            Workbook().add_sheet("bad!name")

    def test_renames_keep_the_sheet_and_change_the_door(self):
        built = book()
        built.rename("Data", "Ledger")
        assert built.sheet("ledger").value_of(ref("A1")) == 42.0
        with pytest.raises(Missing):
            built.sheet("Data")


class TestTheResolver:
    def test_reads_go_through_one_door(self):
        built = book()
        assert built.read("Data", ref("A1")) == 42.0

    def test_the_missing_sheet_wounds_instead_of_raising(self):
        outcome = book().read("Ghost", ref("A1"))
        assert outcome.code == "#REF!"
        assert "wounds instead of raising" in outcome.note


class TestDropping:
    def test_the_damage_is_reported_not_forbidden(self):
        built = book()
        built.sheet("Summary").set_formula(
            ref("C1"), "=1"
        )
        built.sheets["summary"].cells[
            ref("C1").key()
        ].formula_text = "=Data!A1"
        verdict = built.drop_sheet("Data")
        assert "1 formula(s) elsewhere will now read #REF!" in (
            verdict
        )
        assert "delete the husk" in verdict

    def test_the_unread_sheet_drops_quietly(self):
        built = book()
        assert book().drop_sheet("Data").endswith(
            "nobody was reading it"
        )
        assert built.census().startswith("2 sheet(s):")
