"""
EvolutionAnalyzer — deliberately NOT implemented yet.

Per currentplan.docx: "don't hard-code Git analysis yet ... we're
building the final architecture incrementally." This interface exists so
the conformance engine and Finding schema already have a place for
evolution evidence to attach to (Finding.evolution_evidence), without
committing to a Git mining design before it's been thought through
(Milestone 2 in PROGRESS.md).

When implemented, a concrete subclass (e.g. GitEvolutionAnalyzer) will
mine introducing commits, diffs, persistence, and migration patterns for
a given Finding and return structured evolution evidence — see
currentplan.docx §"Later" example: introduced/persisted/ADR/evolution.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EvolutionAnalyzer(ABC):
    """Interface for mining software-evolution evidence for a Finding."""

    @abstractmethod
    def analyze(self, repository_path: str, finding: Any) -> dict | None:
        """Return evolution evidence for `finding`, or None if unavailable.

        Expected shape once implemented (not enforced yet):
            {
                "introducing_commit": "8f31a2",
                "introduced_at": "2026-03-01T00:00:00Z",
                "persisted_commits": 17,
                "related_adr": "ADR-004",
                "interpretation": "temporary migration detected",
            }
        """
        raise NotImplementedError


class NotYetImplementedEvolutionAnalyzer(EvolutionAnalyzer):
    """The only concrete implementation available in Milestone 1.

    Always returns None. Wired into the pipeline now so that swapping in
    a real GitEvolutionAnalyzer later is a one-line change (see
    api/routes/analyze.py), not a redesign.
    """

    def analyze(self, repository_path: str, finding: Any) -> dict | None:
        return None
