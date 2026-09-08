"""Cell styles: named looks that cascade, and never touch the value.

A style is presentation, and the whole discipline of this
module is that presentation and value live in separate
worlds: applying a style, changing a style, or deleting one
never alters what a cell computes, which is why the store
keys styles by cell and holds the value model at arm's
length. Styles cascade in a stated order so a cell's final
look is predictable: the named style it references supplies
defaults, direct per-cell overrides win over that, and an
attribute nobody set is inherited from the base style rather
than left undefined, because an undefined color is a
rendering surprise waiting to differ between screens. A named
style edited in place updates every cell that references it,
which is the reason to have named styles at all, and the
proof that the store holds references and not copies. Deleting
a style that cells still reference is refused with the count
of orphans it would create, because a silent delete leaves
cells pointing at a name that resolves to nothing, and the
alternative, silently reassigning them to the base, hides a
decision the user should make. The base style is the one
floor that cannot be deleted, since a cascade needs a bottom.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid, Missing
from gridiron.refs import CellRef

_ATTRIBUTES = ("bold", "italic", "color", "align")
_BASE = {
    "bold": False,
    "italic": False,
    "color": "black",
    "align": "left",
}


@dataclass
class StyleStore:
    named: dict[str, dict[str, object]] = field(
        default_factory=lambda: {"base": dict(_BASE)}
    )
    cell_style: dict[tuple[int, int], str] = field(
        default_factory=dict
    )
    overrides: dict[
        tuple[int, int], dict[str, object]
    ] = field(default_factory=dict)

    def define(
        self, name: str, attributes: dict[str, object]
    ) -> str:
        title = name.strip().lower()
        if not title:
            raise Invalid("a style needs a name")
        for key in attributes:
            if key not in _ATTRIBUTES:
                raise Invalid(
                    f"{key!r} is not a style attribute; the "
                    f"known ones are {', '.join(_ATTRIBUTES)}"
                )
        self.named[title] = dict(attributes)
        return (
            f"style {title!r} defined with "
            f"{len(attributes)} attribute(s)"
        )

    def apply(self, ref: CellRef, name: str) -> str:
        title = name.strip().lower()
        if title not in self.named:
            raise Missing(
                f"no style named {title!r}; define it first"
            )
        self.cell_style[ref.key()] = title
        return f"{ref.a1()} wears style {title!r}"

    def override(
        self, ref: CellRef, attribute: str, value: object
    ) -> str:
        if attribute not in _ATTRIBUTES:
            raise Invalid(
                f"{attribute!r} is not a style attribute"
            )
        self.overrides.setdefault(ref.key(), {})[
            attribute
        ] = value
        return (
            f"{ref.a1()} overrides {attribute} directly"
        )

    def resolve(self, ref: CellRef) -> dict[str, object]:
        look = dict(self.named["base"])
        style_name = self.cell_style.get(ref.key())
        if style_name is not None:
            look.update(self.named[style_name])
        look.update(self.overrides.get(ref.key(), {}))
        return look

    def _references(self, name: str) -> list[CellRef]:
        return [
            CellRef(row=key[0], col=key[1])
            for key, style in self.cell_style.items()
            if style == name
        ]

    def edit(
        self, name: str, attribute: str, value: object
    ) -> str:
        title = name.strip().lower()
        if title not in self.named:
            raise Missing(f"no style named {title!r}")
        if attribute not in _ATTRIBUTES:
            raise Invalid(
                f"{attribute!r} is not a style attribute"
            )
        self.named[title][attribute] = value
        touched = len(self._references(title))
        return (
            f"style {title!r} updated; {touched} cell(s) "
            "see the change because the store holds "
            "references, not copies"
        )

    def delete(self, name: str) -> str:
        title = name.strip().lower()
        if title == "base":
            raise Invalid(
                "the base style is the cascade's floor and "
                "cannot be deleted"
            )
        if title not in self.named:
            raise Missing(f"no style named {title!r}")
        orphans = self._references(title)
        if orphans:
            addresses = ", ".join(
                sorted(ref.a1() for ref in orphans)
            )
            raise Invalid(
                f"{len(orphans)} cell(s) still wear "
                f"{title!r} ({addresses}); reassign them "
                "before deleting, do not leave them pointing "
                "at nothing"
            )
        del self.named[title]
        return f"style {title!r} deleted"
