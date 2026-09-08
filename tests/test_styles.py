from __future__ import annotations

import pytest

from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef
from gridiron.styles import StyleStore


def ref(text: str) -> CellRef:
    return CellRef.parse(text)


class TestTheCascade:
    def test_an_unstyled_cell_inherits_the_base(self):
        store = StyleStore()
        look = store.resolve(ref("A1"))
        assert look["color"] == "black"
        assert look["bold"] is False

    def test_a_named_style_supplies_defaults(self):
        store = StyleStore()
        store.define("heading", {"bold": True, "color": "navy"})
        store.apply(ref("A1"), "heading")
        look = store.resolve(ref("A1"))
        assert look["bold"] is True
        assert look["color"] == "navy"
        assert look["align"] == "left"

    def test_a_direct_override_wins(self):
        store = StyleStore()
        store.define("heading", {"color": "navy"})
        store.apply(ref("A1"), "heading")
        store.override(ref("A1"), "color", "red")
        assert store.resolve(ref("A1"))["color"] == "red"

    def test_an_unset_attribute_falls_to_the_base(self):
        store = StyleStore()
        store.define("loud", {"bold": True})
        store.apply(ref("A1"), "loud")
        assert store.resolve(ref("A1"))["align"] == "left"


class TestNamedStyleEditing:
    def test_editing_a_style_moves_every_cell(self):
        store = StyleStore()
        store.define("money", {"align": "right"})
        store.apply(ref("A1"), "money")
        store.apply(ref("A2"), "money")
        verdict = store.edit("money", "color", "green")
        assert "2 cell(s) see the change" in verdict
        assert store.resolve(ref("A1"))["color"] == "green"
        assert store.resolve(ref("A2"))["color"] == "green"

    def test_editing_an_unknown_style_is_missing(self):
        store = StyleStore()
        with pytest.raises(Missing):
            store.edit("ghost", "bold", True)


class TestDeletion:
    def test_deleting_a_referenced_style_is_refused(self):
        store = StyleStore()
        store.define("temp", {"bold": True})
        store.apply(ref("A1"), "temp")
        with pytest.raises(Invalid) as caught:
            store.delete("temp")
        assert "still wear" in str(caught.value)
        assert "A1" in str(caught.value)

    def test_an_unreferenced_style_deletes(self):
        store = StyleStore()
        store.define("temp", {"bold": True})
        assert "deleted" in store.delete("temp")

    def test_the_base_cannot_be_deleted(self):
        store = StyleStore()
        with pytest.raises(Invalid) as caught:
            store.delete("base")
        assert "cascade's floor" in str(caught.value)


class TestRefusals:
    def test_an_unknown_attribute_is_refused(self):
        store = StyleStore()
        with pytest.raises(Invalid) as caught:
            store.define("x", {"font": "comic"})
        assert "not a style attribute" in str(caught.value)

    def test_applying_an_undefined_style_is_missing(self):
        store = StyleStore()
        with pytest.raises(Missing):
            store.apply(ref("A1"), "nope")
