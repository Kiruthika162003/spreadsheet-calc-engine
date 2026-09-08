from __future__ import annotations

from gridiron.evaluate import evaluate
from gridiron.library import full_table
from gridiron.parser import parse_formula


def run(formula: str):
    return evaluate(
        parse_formula(formula), lambda _r: None, full_table
    )


class TestErrDistinctions:
    def test_iserr_excludes_na(self):
        assert run("=ISERR(1/0)") is True
        assert run("=ISERR(NA())") is False

    def test_isna_is_the_complement(self):
        assert run("=ISNA(NA())") is True
        assert run("=ISNA(1/0)") is False


class TestParity:
    def test_even_and_odd(self):
        assert run("=ISEVEN(4)") is True
        assert run("=ISODD(4)") is False
        assert run("=ISODD(7)") is True

    def test_parity_truncates(self):
        assert run("=ISEVEN(4.9)") is True

    def test_a_non_number_does_not_parse(self):
        outcome = run('=ISEVEN("x")')
        assert outcome.code == "#VALUE!"


class TestCoercion:
    def test_n_forces_a_number(self):
        assert run("=N(TRUE)") == 1.0
        assert run('=N("text")') == 0.0
        assert run("=N(5)") == 5.0

    def test_t_forces_text(self):
        assert run('=T("hi")') == "hi"
        assert run("=T(5)") == ""


class TestMisc:
    def test_na_produces_the_error(self):
        assert run("=NA()").code == "#N/A"

    def test_na_takes_no_arguments(self):
        assert run("=NA(1)").code == "#VALUE!"

    def test_type_names_the_kind(self):
        assert run("=TYPE(5)") == 1.0
        assert run('=TYPE("x")') == 2.0
        assert run("=TYPE(TRUE)") == 4.0
        assert run("=TYPE(1/0)") == 16.0

    def test_isnontext(self):
        assert run("=ISNONTEXT(5)") is True
        assert run('=ISNONTEXT("x")') is False
