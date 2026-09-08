"""Vectors: dot, cross, norm, and the angle between, each guarding its domain.

Vector columns show up wherever a spreadsheet touches
physics or graphics, and the four operations here each have a
domain edge that a careless version steps off. The dot
product and the norm work in any dimension and are plain
sums. The cross product is defined only in three dimensions,
so it refuses vectors of any other length by name rather
than silently producing a two-dimensional scalar or ignoring
extra components, because a cross product of four-vectors is
a question with no answer, not a hard case. The angle between
two vectors is the arccosine of their normalized dot product,
and it carries two guards: a zero-length vector has no
direction and therefore no angle to anything, refused rather
than returning a nan, and the cosine is clamped into minus-
one-to-one before the arccosine, because floating-point
rounding on nearly parallel vectors can nudge the ratio a
hair past one and hand the arccosine a value outside its
domain, turning a zero-degree angle into a math error. The
angle comes back in radians, the mathematical default, with
the caller free to convert, matching the trig family's
convention rather than inventing a degrees-here surprise.
Lengths must match for the dot product and the angle, refused
by their two numbers otherwise, because pairing a
three-vector with a two-vector adds a component that is not
there.
"""

from __future__ import annotations

import math

from gridiron.errors import Invalid


def _check_same(a: list[float], b: list[float]) -> None:
    if len(a) != len(b):
        raise Invalid(
            f"vectors of length {len(a)} and {len(b)} do "
            "not pair; the missing component is not zero, "
            "it is absent"
        )


def dot(a: list[float], b: list[float]) -> float:
    _check_same(a, b)
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(a: list[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def cross(a: list[float], b: list[float]) -> list[float]:
    if len(a) != 3 or len(b) != 3:
        raise Invalid(
            "the cross product is defined only in three "
            "dimensions; a cross of other lengths has no "
            "answer, not a hard case"
        )
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def angle_between(a: list[float], b: list[float]) -> float:
    _check_same(a, b)
    na, nb = norm(a), norm(b)
    if na == 0 or nb == 0:
        raise Invalid(
            "a zero-length vector has no direction and so no "
            "angle to anything"
        )
    cosine = dot(a, b) / (na * nb)
    cosine = max(-1.0, min(1.0, cosine))
    return math.acos(cosine)
