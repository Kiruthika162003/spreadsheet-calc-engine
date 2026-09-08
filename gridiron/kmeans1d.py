"""One-dimensional k-means: grouping numbers into clusters, reproducibly.

Clustering a column of numbers into k groups is k-means, and
in one dimension it is simple enough to do exactly and
honestly. The trap in every k-means is the starting point:
the algorithm converges to a local optimum that depends on
where the centroids began, so a run that seeded them randomly
would give a different answer every time and a clustering
nobody could reproduce. This module seeds deterministically
at evenly spaced ranks of the sorted data rather than evenly
across its value range, so the same data and the same k
always give the same clusters and the result can be
regenerated and checked. The rank choice matters: spreading
seeds across the raw value range drops a centroid into the
empty gap between two tight clusters and it starves, which
the first draft did and which left a real three-group column
with an empty middle cluster; seeding at the data's own
quantiles puts every centroid on an actual value and finds
the natural groups.
It iterates the standard assign-then-recenter loop until the
assignments stop changing or a bound is reached, and it
returns the centroids and each point's cluster, so a caller
sees both the groups and where they sit. Asking for more
clusters than there are distinct values is refused, because k
clusters need k distinct points to sit on and forcing more
produces empty clusters that the algorithm then divides by
zero to recenter. An empty cluster mid-run, which can happen
when two seeds land on the same crowded region, is handled by
leaving that centroid where it was rather than moving it to
the mean of nothing, so the loop never divides by an empty
count. The within-cluster sum of squares is reported because
it is how a caller compares k values to choose one, the elbow
the whole method leans on.
"""

from __future__ import annotations

from dataclasses import dataclass

from gridiron.errors import Invalid


@dataclass
class ClusterResult:
    centroids: list[float]
    assignments: list[int]
    inertia: float


def _nearest(value: float, centroids: list[float]) -> int:
    best = 0
    best_distance = abs(value - centroids[0])
    for index in range(1, len(centroids)):
        distance = abs(value - centroids[index])
        if distance < best_distance:
            best_distance = distance
            best = index
    return best


def cluster(
    values: list[float], k: int, max_iterations: int = 100
) -> ClusterResult:
    if k < 1:
        raise Invalid("k must be at least one")
    distinct = sorted(set(values))
    if k > len(distinct):
        raise Invalid(
            f"cannot make {k} clusters from "
            f"{len(distinct)} distinct value(s); the extras "
            "would be empty clusters divided by zero"
        )
    if k == 1:
        centroids = [sum(values) / len(values)]
    else:
        ordered = sorted(values)
        centroids = [
            ordered[
                round(i * (len(ordered) - 1) / (k - 1))
            ]
            for i in range(k)
        ]
        # Distinct seeds guaranteed by the distinct-count
        # guard above; nudge any duplicate off its twin.
        for i in range(1, k):
            if centroids[i] <= centroids[i - 1]:
                centroids[i] = centroids[i - 1] + 1e-9
    assignments = [0] * len(values)
    for _ in range(max_iterations):
        new_assignments = [
            _nearest(v, centroids) for v in values
        ]
        if new_assignments == assignments:
            break
        assignments = new_assignments
        for index in range(k):
            members = [
                values[i]
                for i in range(len(values))
                if assignments[i] == index
            ]
            if members:
                centroids[index] = sum(members) / len(
                    members
                )
    inertia = sum(
        (values[i] - centroids[assignments[i]]) ** 2
        for i in range(len(values))
    )
    return ClusterResult(
        centroids=centroids,
        assignments=assignments,
        inertia=inertia,
    )
