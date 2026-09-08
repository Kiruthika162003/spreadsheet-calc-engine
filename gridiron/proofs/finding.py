"""Findings: what a proof claimed, what it measured, whether it holds."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    proof: str
    claim: str
    numbers: dict
    holds: bool

    def line(self) -> str:
        state = "holds" if self.holds else "BROKEN"
        return f"{self.proof}: {state}: {self.claim}"
