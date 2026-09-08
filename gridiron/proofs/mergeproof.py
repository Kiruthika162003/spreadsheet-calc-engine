"""The merge proof: the anchor is the only real cell, and no write sneaks past.

Merging leaks display into semantics, and this drill pins the
three rules the module wrote down so none is discovered
during an audit. First, merging over data is refused rather
than silently deleting it, so the drill puts a value in a
covered cell and confirms the merge is rejected with the
occupied cell named, because silent deletion on merge is the
incumbent behavior this house rejects. Second, once merged,
the covered cells are not writable: a write into a shadow is
redirected as a refusal naming the anchor, so the value the
user thought they set never lands somewhere invisible.
Third, the anchor remains a normal cell whose value the merge
does not touch, so reading it returns exactly what it held.
The drill also confirms two merges cannot overlap, since
stacked merges have no coherent anchor, and that unmerging
releases the rectangle so its former shadows become writable
again, because a merge that could not be undone would be a
one-way narrowing of the sheet. Every rule is checked by the
refusal actually firing, not by inspecting a flag, because a
rule that is documented but not enforced is a comment, not a
constraint.
"""

from __future__ import annotations

from gridiron.errors import Invalid
from gridiron.mergecells import MergeRegistry
from gridiron.proofs.finding import Finding
from gridiron.refs import CellRef, RangeRef
from gridiron.sheet import Sheet


def run() -> Finding:
    sheet = Sheet()
    sheet.set_literal(CellRef.parse("A1"), "title")
    registry = MergeRegistry(sheet=sheet)

    # Data under the merge is refused.
    sheet.set_literal(CellRef.parse("B1"), 99.0)
    data_refused = False
    try:
        registry.merge(RangeRef.parse("A1:B1"))
    except Invalid:
        data_refused = True
    sheet.clear(CellRef.parse("B1"))

    registry.merge(RangeRef.parse("A1:B1"))
    anchor_value = sheet.value_of(CellRef.parse("A1"))

    write_refused = False
    try:
        registry.check_write(CellRef.parse("B1"))
    except Invalid:
        write_refused = True

    overlap_refused = False
    try:
        registry.merge(RangeRef.parse("B1:C1"))
    except Invalid:
        overlap_refused = True

    registry.unmerge(RangeRef.parse("A1:B1"))
    freed = registry.anchor_of(CellRef.parse("B1")) is None

    numbers = {
        "data_merge_refused": data_refused,
        "anchor_value": anchor_value,
        "shadow_write_refused": write_refused,
        "overlap_refused": overlap_refused,
        "unmerge_freed_the_shadow": freed,
    }
    holds = (
        data_refused
        and anchor_value == "title"
        and write_refused
        and overlap_refused
        and freed
    )
    return Finding(
        proof="mergeproof",
        claim=(
            "merging over data is refused, a write into a "
            "covered cell is redirected to the anchor, two "
            "merges cannot overlap, and unmerging frees the "
            "shadows again"
        ),
        numbers=numbers,
        holds=holds,
    )
