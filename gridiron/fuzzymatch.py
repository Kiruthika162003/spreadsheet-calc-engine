"""Fuzzy matching: edit distance, and a best guess that knows when to abstain.

Reconciling two lists of names typed by different people is
the chore fuzzy matching exists for, and the honest version
of it does one thing the eager version does not: it abstains.
The edit distance is the classic Levenshtein count of single-
character insertions, deletions, and substitutions, computed
with the standard dynamic-programming table, and it is exact,
not an approximation. The similarity ratio derived from it is
one minus the distance over the longer length, so identical
strings score one and completely different ones approach
zero. The best-match finder is where abstention lives: it
returns the closest candidate only when its similarity clears
a stated threshold, and returns nothing when the best guess
is still a bad guess, because a fuzzy match that always
returns its closest option will cheerfully map Smith to
Smyth and also Smith to Jones, and the second is worse than
no answer. Case is folded before comparison because Ada and
ADA are the same name typed twice, but the fold is stated
rather than assumed, and ties at the top similarity are
broken toward the earlier candidate rather than chosen
arbitrarily, so the same inputs always give the same match
and a reconciliation is reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass


def edit_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, lchar in enumerate(left, start=1):
        current = [i]
        for j, rchar in enumerate(right, start=1):
            cost = 0 if lchar == rchar else 1
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + cost,
                )
            )
        previous = current
    return previous[-1]


def similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    distance = edit_distance(left, right)
    longest = max(len(left), len(right))
    return 1.0 - distance / longest


@dataclass(frozen=True)
class Match:
    candidate: str
    score: float


def best_match(
    needle: str,
    candidates: list[str],
    threshold: float = 0.6,
    fold_case: bool = True,
) -> Match | None:
    target = needle.upper() if fold_case else needle
    best: Match | None = None
    for candidate in candidates:
        other = (
            candidate.upper() if fold_case else candidate
        )
        score = similarity(target, other)
        if best is None or score > best.score:
            best = Match(candidate=candidate, score=score)
    if best is not None and best.score >= threshold:
        return best
    return None
