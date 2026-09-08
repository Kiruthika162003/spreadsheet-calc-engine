from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.geometry import (
    area,
    distance,
    orientation,
    point_in_polygon,
    signed_area,
)

SQUARE = [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)]


class TestDistance:
    def test_the_three_four_five_triangle(self):
        assert distance((0.0, 0.0), (3.0, 4.0)) == 5.0

    def test_zero_distance_to_self(self):
        assert distance((2.0, 2.0), (2.0, 2.0)) == 0.0


class TestArea:
    def test_the_unit_square(self):
        assert area(SQUARE) == 16.0

    def test_a_triangle(self):
        assert area(
            [(0.0, 0.0), (4.0, 0.0), (0.0, 3.0)]
        ) == 6.0

    def test_orientation_reads_the_sign(self):
        assert orientation(SQUARE) == "counterclockwise"
        clockwise = list(reversed(SQUARE))
        assert orientation(clockwise) == "clockwise"

    def test_the_signed_area_keeps_the_sign(self):
        assert signed_area(SQUARE) > 0
        assert signed_area(list(reversed(SQUARE))) < 0

    def test_too_few_vertices_is_refused(self):
        with pytest.raises(Invalid) as caught:
            area([(0.0, 0.0), (1.0, 1.0)])
        assert "no inside" in str(caught.value)


class TestPointInPolygon:
    def test_a_point_inside(self):
        assert point_in_polygon((2.0, 2.0), SQUARE) is True

    def test_a_point_outside(self):
        assert point_in_polygon((5.0, 5.0), SQUARE) is False

    def test_a_point_on_an_edge_is_inside(self):
        assert point_in_polygon((4.0, 2.0), SQUARE) is True

    def test_a_vertex_is_inside(self):
        assert point_in_polygon((0.0, 0.0), SQUARE) is True

    def test_a_concave_polygon(self):
        # An L-shape; the notch is outside.
        ell = [
            (0.0, 0.0),
            (4.0, 0.0),
            (4.0, 2.0),
            (2.0, 2.0),
            (2.0, 4.0),
            (0.0, 4.0),
        ]
        assert point_in_polygon((3.0, 3.0), ell) is False
        assert point_in_polygon((1.0, 1.0), ell) is True
