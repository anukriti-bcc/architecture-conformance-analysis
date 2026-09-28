"""
SemanticAnalyzer — deliberately NOT implemented yet.

Per currentplan.docx: "we don't yet know which model, what context it
needs, what exact task it performs, what the escalation algorithm will
be, how we'll evaluate it, or what evidence it should receive... If we
hard-code an LLM into the architecture now, we risk building the wrong
thing."

This interface is the clean boundary the LLM layer will plug into later
(Milestone 4), via the `POST /findings/{id}/semantic-analysis` endpoint,
which currently returns 501 Not Implemented.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SemanticAnalyzer(ABC):
    """Interface for LLM-based semantic analysis of an ambiguous Finding."""

    @abstractmethod
    def analyze(self, finding: Any, evidence: dict) -> dict | None:
        """Return a semantic verdict for `finding` given aggregated
        evidence, or None if analysis could not be completed.

        Expected shape once implemented (not enforced yet):
            {
                "verdict": "legitimate_migration" | "violation" | "uncertain",
                "explanation": "...",
                "model": "...",
                "tokens_used": {"input": ..., "output": ...},
            }
        """
        raise NotImplementedError


class NotYetImplementedSemanticAnalyzer(SemanticAnalyzer):
    """The only concrete implementation available in Milestone 1. Always
    returns None — no model has been chosen yet (intentional)."""

    def analyze(self, finding: Any, evidence: dict) -> dict | None:
        return None
