"""The dependency graph as DOT: the workbook's plumbing, drawn deterministic.

A dependency graph in text form answers the question every
reviewer eventually asks, what feeds what, in a format the
whole tooling world already renders. The emitter's first
rule is determinism: nodes and edges are sorted by address,
because a graph that shuffles between runs diffs as churn
and churn hides the one edge that actually changed. Formula
cells show their formula under their address, literal cells
show their value, and cells currently holding an error are
drawn filled so the wound is visible in the picture, not
just in the grid. Ranges get one node each rather than an
edge per member cell, since a SUM over a thousand rows drawn
as a thousand arrows is a hairball posing as documentation;
the range node's shape says it is a region and its single
edge says who watches it. A focus cell restricts the drawing
to that cell's ancestors and descendants, the cone a
reviewer actually cares about when one number looks wrong,
and focusing on a cell the graph does not know is refused by
name rather than drawn as an empty page.
"""

from __future__ import annotations

from gridiron.engine import Engine
from gridiron.errors import Missing
from gridiron.refs import CellRef
from gridiron.values import is_error, render


def _label(engine: Engine, key: tuple[int, int]) -> str:
    ref = CellRef(row=key[0], col=key[1])
    cell = engine.sheet.cells.get(key)
    if cell is None:
        return ref.a1()
    if cell.formula_text is not None:
        return f"{ref.a1()}\\n{cell.formula_text}"
    return f"{ref.a1()}\\n{render(cell.literal)}"


def _edges(
    engine: Engine,
) -> tuple[
    set[tuple[str, str]], set[str], set[tuple[int, int]]
]:
    edges: set[tuple[str, str]] = set()
    ranges: set[str] = set()
    cell_keys: set[tuple[int, int]] = set()
    for ref, cell in engine.sheet.formula_cells():
        target = ref.a1()
        cell_keys.add(ref.key())
        for precedent in cell.tree.refs():
            if isinstance(precedent, CellRef):
                edges.add((precedent.a1(), target))
                cell_keys.add(precedent.key())
            else:
                region = precedent.a1()
                ranges.add(region)
                edges.add((region, target))
    return edges, ranges, cell_keys


def _cone(
    edges: set[tuple[str, str]], focus: str
) -> set[str]:
    keep = {focus}
    grew = True
    while grew:
        grew = False
        for source, target in edges:
            if target in keep and source not in keep:
                keep.add(source)
                grew = True
            if source in keep and target not in keep:
                keep.add(target)
                grew = True
    return keep


def dot_graph(
    engine: Engine, focus: CellRef | None = None
) -> str:
    edges, ranges, cell_keys = _edges(engine)
    names = {CellRef(row=k[0], col=k[1]).a1() for k in cell_keys}
    if focus is not None:
        if focus.a1() not in names:
            raise Missing(
                f"{focus.a1()} is not in the graph; an "
                "empty page is not a drawing"
            )
        keep = _cone(edges, focus.a1())
        edges = {
            (s, t)
            for s, t in edges
            if s in keep and t in keep
        }
        ranges = {r for r in ranges if r in keep}
        cell_keys = {
            k
            for k in cell_keys
            if CellRef(row=k[0], col=k[1]).a1() in keep
        }
    lines = ["digraph workbook {", "  rankdir=LR;"]
    for key in sorted(cell_keys):
        ref = CellRef(row=key[0], col=key[1])
        label = _label(engine, key)
        value = engine.value(ref)
        if is_error(value):
            lines.append(
                f'  "{ref.a1()}" [label="{label}" '
                'style=filled fillcolor=lightpink];'
            )
        else:
            lines.append(
                f'  "{ref.a1()}" [label="{label}"];'
            )
    for region in sorted(ranges):
        lines.append(
            f'  "{region}" [shape=box3d];'
        )
    for source, target in sorted(edges):
        lines.append(f'  "{source}" -> "{target}";')
    lines.append("}")
    return "\n".join(lines)
