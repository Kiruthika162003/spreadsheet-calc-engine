from __future__ import annotations

import pytest

from gridiron.errors import Invalid, Missing
from gridiron.evaluate import evaluate
from gridiron.hyperlinks import (
    LinkRegistry,
    hyperlink_function,
)
from gridiron.library import full_table
from gridiron.parser import parse_formula
from gridiron.refs import CellRef


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


class TestTheRegistry:
    def test_a_safe_external_link(self):
        reg = LinkRegistry()
        verdict = reg.set_link(
            ref("A1"), "https://example.com"
        )
        assert "external" in verdict
        assert reg.target_of(ref("A1")).kind == "external"

    def test_an_internal_cell_reference(self):
        reg = LinkRegistry()
        reg.set_link(ref("A1"), "Sheet2!B4")
        assert reg.target_of(ref("A1")).kind == "internal"

    def test_a_dangerous_scheme_is_refused(self):
        reg = LinkRegistry()
        with pytest.raises(Invalid) as caught:
            reg.set_link(
                ref("A1"), "javascript:alert(1)"
            )
        assert "carries an attack" in str(caught.value)

    def test_an_unknown_scheme_is_refused(self):
        reg = LinkRegistry()
        with pytest.raises(Invalid) as caught:
            reg.set_link(ref("A1"), "ftp://host/file")
        assert "allowlist" in str(caught.value)

    def test_a_bare_typo_is_neither_url_nor_cell(self):
        reg = LinkRegistry()
        with pytest.raises(Invalid) as caught:
            reg.set_link(ref("A1"), "not a place")
        assert "typo, not a destination" in str(caught.value)

    def test_removing_leaves_the_label(self):
        reg = LinkRegistry()
        reg.set_link(ref("A1"), "https://example.com")
        assert "untouched" in reg.remove(ref("A1"))
        assert reg.target_of(ref("A1")) is None

    def test_removing_an_unlinked_cell_is_missing(self):
        reg = LinkRegistry()
        with pytest.raises(Missing):
            reg.remove(ref("Z9"))

    def test_the_census_splits_the_kinds(self):
        reg = LinkRegistry()
        reg.set_link(ref("A1"), "https://a.com")
        reg.set_link(ref("A2"), "B4")
        assert reg.census() == (
            "2 link(s): 1 external, 1 internal"
        )


class TestTheFunction:
    def _run(self, reg, anchor, formula):
        install = hyperlink_function(reg)
        table = lambda name: (  # noqa: E731
            install(anchor)
            if name == "HYPERLINK"
            else full_table(name)
        )
        return evaluate(
            parse_formula(formula),
            lambda _r: None,
            table,
        )

    def test_the_value_is_the_label(self):
        reg = LinkRegistry()
        out = self._run(
            reg,
            ref("A1"),
            '=HYPERLINK("https://x.com", "click")',
        )
        assert out == "click"
        assert reg.target_of(ref("A1")).target == (
            "https://x.com"
        )

    def test_without_a_label_the_value_is_the_target(self):
        reg = LinkRegistry()
        out = self._run(
            reg, ref("A1"), '=HYPERLINK("https://x.com")'
        )
        assert out == "https://x.com"

    def test_a_dangerous_target_errors_the_cell(self):
        reg = LinkRegistry()
        out = self._run(
            reg,
            ref("A1"),
            '=HYPERLINK("javascript:evil", "safe?")',
        )
        assert out.code == "#VALUE!"
        assert "carries an attack" in out.note
