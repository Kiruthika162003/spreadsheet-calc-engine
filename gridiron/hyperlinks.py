"""Hyperlinks: a display string that computes, a target that is checked once.

HYPERLINK is a function that returns text, and that is the
whole trick to keeping it honest: the cell's value is the
friendly label, computed like any string, while the target
lives in a side registry keyed by cell, so a formula that
concatenates a label stays a formula about a label and never
smuggles a URL into the arithmetic. The target is checked
when it is set, not when it is clicked, because a link that
validates late is a link that ships broken. The scheme
allowlist is the security boundary and it is small on
purpose: http, https, and mailto pass, an in-workbook target
like a sheet-and-cell reference passes as an internal jump,
and everything else, javascript and data and file schemes
especially, is refused by name, because a spreadsheet that
will build a javascript: link is a spreadsheet that will
carry an attack to whoever opens it. A target with no scheme
is treated as an internal reference and validated as an A1
address or a sheet bang address, refused if it parses as
neither, since a bare string that is neither a URL nor a
cell is a typo, not a destination. Removing a cell's link
leaves its label untouched, because the words were never the
link, and that separation is the point.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from gridiron.errors import Invalid, Missing
from gridiron.evaluate import evaluate
from gridiron.refs import CellRef
from gridiron.values import ErrorValue, is_error

_SAFE_SCHEMES = ("http://", "https://", "mailto:")
_DANGEROUS = ("javascript:", "data:", "file:", "vbscript:")


def _classify_target(target: str) -> str:
    lowered = target.strip().lower()
    if not lowered:
        raise Invalid("a link needs a target")
    for scheme in _DANGEROUS:
        if lowered.startswith(scheme):
            raise Invalid(
                f"the {scheme} scheme is refused; a "
                "spreadsheet that builds one carries an "
                "attack to whoever opens it"
            )
    for scheme in _SAFE_SCHEMES:
        if lowered.startswith(scheme):
            return "external"
    if "://" in lowered:
        raise Invalid(
            f"the scheme in {target!r} is not on the "
            "allowlist of http, https, and mailto"
        )
    return _classify_internal(target)


def _classify_internal(target: str) -> str:
    body = target.strip()
    if body.startswith("#"):
        body = body[1:]
    if "!" in body:
        sheet, _, cell = body.partition("!")
        if not sheet or not cell:
            raise Invalid(
                f"{target!r} is neither a URL nor a whole "
                "sheet reference"
            )
        _require_cell(cell, target)
        return "internal"
    _require_cell(body, target)
    return "internal"


def _require_cell(text: str, original: str) -> None:
    try:
        CellRef.parse(text.upper())
    except Invalid as refusal:
        raise Invalid(
            f"{original!r} is neither a URL nor a cell "
            "address; a bare string that is neither is a "
            "typo, not a destination"
        ) from refusal


@dataclass(frozen=True)
class Link:
    target: str
    kind: str


@dataclass
class LinkRegistry:
    links: dict[tuple[int, int], Link] = field(
        default_factory=dict
    )

    def set_link(self, ref: CellRef, target: str) -> str:
        kind = _classify_target(target)
        self.links[ref.key()] = Link(
            target=target.strip(), kind=kind
        )
        return (
            f"{ref.a1()} links to an {kind} target"
        )

    def target_of(self, ref: CellRef) -> Link | None:
        return self.links.get(ref.key())

    def remove(self, ref: CellRef) -> str:
        if ref.key() not in self.links:
            raise Missing(f"{ref.a1()} carries no link")
        del self.links[ref.key()]
        return (
            f"{ref.a1()} unlinked; its label is untouched "
            "because the words were never the link"
        )

    def census(self) -> str:
        external = sum(
            1
            for link in self.links.values()
            if link.kind == "external"
        )
        internal = len(self.links) - external
        return (
            f"{len(self.links)} link(s): {external} "
            f"external, {internal} internal"
        )


def hyperlink_function(registry: LinkRegistry):
    """A HYPERLINK that binds the target into `registry` for `anchor`."""

    def install(anchor: CellRef):
        def run(args, lookup, functions, names):
            if len(args) not in (1, 2):
                return ErrorValue(
                    code="#VALUE!",
                    note="HYPERLINK takes a target and an "
                    "optional label",
                )
            target = evaluate(
                args[0], lookup, functions, names
            )
            if is_error(target):
                return target
            if not isinstance(target, str):
                return ErrorValue(
                    code="#VALUE!",
                    note="a link target is text",
                )
            try:
                registry.set_link(anchor, target)
            except Invalid as refusal:
                return ErrorValue(
                    code="#VALUE!", note=str(refusal)
                )
            if len(args) == 2:
                return evaluate(
                    args[1], lookup, functions, names
                )
            return target

        return run

    return install
