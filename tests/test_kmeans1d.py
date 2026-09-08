from __future__ import annotations

import pytest

from gridiron.errors import Invalid
from gridiron.kmeans1d import cluster

THREE_GROUPS = [
    1.0, 1.5, 2.0,
    10.0, 10.5, 11.0,
    50.0, 51.0,
]


class TestClustering:
    def test_it_finds_the_natural_groups(self):
        result = cluster(THREE_GROUPS, 3)
        assert result.assignments == [
            0, 0, 0, 1, 1, 1, 2, 2,
        ]

    def test_the_centroids_sit_on_the_groups(self):
        result = cluster(THREE_GROUPS, 3)
        assert result.centroids[0] == pytest.approx(1.5)
        assert result.centroids[1] == pytest.approx(10.5)
        assert result.centroids[2] == pytest.approx(50.5)

    def test_a_single_cluster_is_the_mean(self):
        result = cluster([2.0, 4.0, 6.0], 1)
        assert result.centroids == [pytest.approx(4.0)]


class TestReproducibility:
    def test_the_same_data_clusters_the_same(self):
        a = cluster(THREE_GROUPS, 3)
        b = cluster(THREE_GROUPS, 3)
        assert a.centroids == b.centroids
        assert a.assignments == b.assignments


class TestInertia:
    def test_inertia_falls_with_more_clusters(self):
        inertias = [
            cluster(THREE_GROUPS, k).inertia
            for k in (1, 2, 3)
        ]
        assert inertias[0] > inertias[1] > inertias[2]

    def test_the_elbow_is_at_three(self):
        # The big drop lands going to three groups.
        drop_to_three = (
            cluster(THREE_GROUPS, 2).inertia
            - cluster(THREE_GROUPS, 3).inertia
        )
        drop_to_four = (
            cluster(THREE_GROUPS, 3).inertia
            - cluster(THREE_GROUPS, 4).inertia
        )
        assert drop_to_three > drop_to_four


class TestRefusals:
    def test_too_many_clusters_is_refused(self):
        with pytest.raises(Invalid) as caught:
            cluster([1.0, 2.0], 5)
        assert "empty clusters" in str(caught.value)

    def test_zero_clusters_is_refused(self):
        with pytest.raises(Invalid):
            cluster([1.0, 2.0], 0)
