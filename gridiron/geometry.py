"""Geometry: distances, the shoelace area, and whether a point is inside.

Coordinate columns show up in spreadsheets more than one
expects, survey points, store locations, sensor positions,
and three questions follow them: how far apart, how much
area does a boundary enclose, and is this point inside that
boundary. Distance is the plain Euclidean length. The area of
a polygon is the shoelace formula, the signed sum of the
cross products of consecutive vertices halved, and the sign
is information worth keeping rather than discarding: a
positive area means the vertices wind counterclockwise and a
negative one clockwise, so the absolute value is the area and
the sign is the orientation, and a caller who needs to know
which way a boundary was drawn should not have to recompute
it. A polygon of fewer than three vertices encloses no area
and is refused, because two points make a line and a line has
no inside. Point-in-polygon uses the ray-casting rule,
counting how many times a ray from the point crosses the
edges, inside when the count is odd, and the boundary case is
stated rather than left to chance: a point exactly on an edge
is reported as inside, because a fence post is part of the
property, and leaving the on-edge answer to floating-point
luck is how the same point tests inside on one machine and
out on another.
"""

from __future__ import annotations

import math

from gridiron.errors import Invalid

Point = tuple[float, float]


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def signed_area(vertices: list[Point]) -> float:
    if len(vertices) < 3:
        raise Invalid(
            "a polygon needs at least three vertices; two "
            "points make a line and a line has no inside"
        )
    total = 0.0
    n = len(vertices)
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return total / 2


def area(vertices: list[Point]) -> float:
    return abs(signed_area(vertices))


def orientation(vertices: list[Point]) -> str:
    signed = signed_area(vertices)
    if signed > 0:
        return "counterclockwise"
    if signed < 0:
        return "clockwise"
    return "degenerate"


def _on_segment(
    point: Point, a: Point, b: Point
) -> bool:
    cross = (b[0] - a[0]) * (point[1] - a[1]) - (
        b[1] - a[1]
    ) * (point[0] - a[0])
    if abs(cross) > 1e-12:
        return False
    within_x = min(a[0], b[0]) - 1e-12 <= point[0] <= (
        max(a[0], b[0]) + 1e-12
    )
    within_y = min(a[1], b[1]) - 1e-12 <= point[1] <= (
        max(a[1], b[1]) + 1e-12
    )
    return within_x and within_y


def point_in_polygon(
    point: Point, vertices: list[Point]
) -> bool:
    if len(vertices) < 3:
        raise Invalid(
            "a polygon needs at least three vertices"
        )
    n = len(vertices)
    for i in range(n):
        if _on_segment(
            point, vertices[i], vertices[(i + 1) % n]
        ):
            return True
    inside = False
    px, py = point
    for i in range(n):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            crossing_x = (
                x1 + (py - y1) / (y2 - y1) * (x2 - x1)
            )
            if px < crossing_x:
                inside = not inside
    return inside
