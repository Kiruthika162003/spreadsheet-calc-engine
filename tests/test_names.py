from __future__ import annotations

import pytest

from gridiron.errors import Invalid, Missing
from gridiron.evaluate import evaluate
from gridiron.functions import builtin_table
from gridiron.names import NameRegistry
from gridiron.parser import parse_formula
from gridiron.refs import CellRef

WORLD = {(6, 1): 200.0, (16, 5): 0.19}


def lookup(ref: CellRef):
    return WORLD.get(ref.key())


def registry() -> NameRegistry:
    names = NameRegistry()
    names.define("REVENUE", "=B7")
    names.define("TAXRATE", "=F17")
    return names


def run(formula: str, names: NameRegistry):
    return evaluate(
        parse_formula(formula),
        lookup,
        builtin_table,
        names.lookup,
    )


class TestResolution:
    def test_the_readable_formula_computes(self):
        names = registry()
        assert run("=REVENUE*TAXRATE", names) == 38.0

    def test_names_can_bind_constants_and_expressions(self):
        names = NameRegistry()
        names.define("DOZEN", "=12")
        names.define("GROSS", "=DOZEN*DOZEN")
        assert run("=GROSS+DOZEN", names) == 156.0

    def test_the_forgotten_name_says_name_not_last_value(self):
        names = registry()
        names.forget("TAXRATE")
        outcome = run("=REVENUE*TAXRATE", names)
        assert outcome.code == "#NAME?"


class TestTheGrammar:
    def test_an_addressable_name_would_make_the_parser_guess(self):
        with pytest.raises(Invalid) as caught:
            NameRegistry().define("B12", "=1")
        assert "guessing is banned in this codebase" in str(
            caught.value
        )

    def test_illegal_spellings_are_refused(self):
        for name in ("2TAX", "TAX RATE", "TAX-RATE", ""):
            with pytest.raises(Invalid):
                NameRegistry().define(name, "=1")

    def test_case_folds_to_one_name(self):
        names = NameRegistry()
        names.define("TaxRate", "=1")
        with pytest.raises(Invalid):
            names.define("TAXRATE", "=2")


class TestLifecycle:
    def test_redefinition_goes_through_replace(self):
        names = registry()
        with pytest.raises(Invalid):
            names.define("TAXRATE", "=F18")
        names.replace("TAXRATE", "=0.25")
        assert run("=TAXRATE", names) == 0.25

    def test_replacing_or_forgetting_the_undefined_is_missing(self):
        with pytest.raises(Missing):
            NameRegistry().replace("GHOST", "=1")
        with pytest.raises(Missing):
            NameRegistry().forget("GHOST")


class TestTheCensus:
    def test_the_api_deserves_a_page(self):
        census = registry().census()
        assert census.startswith(
            "2 name(s), the workbook's API:"
        )
        assert "  REVENUE = B7" in census

    def test_the_empty_census_is_honest(self):
        assert NameRegistry().census() == (
            "no names defined; every formula is addresses"
        )
