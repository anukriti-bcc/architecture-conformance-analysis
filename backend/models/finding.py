"""
The Finding object is the central artifact of the whole system.

Milestone 1 only populates `structural_evidence`. The other evidence
slots exist now, set to None, so later milestones (evolution mining,
architectural-intent extraction beyond raw rules, semantic/LLM analysis)
can attach evidence to the *same* object rather than requiring a data
model migration. See currentplan.docx, section 9, for the rationale.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from models.component import Dependency


class FindingStatus(str, Enum):
    VIOLATION = "violation"
    CONFORMANT = "conformant"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNSET = "unset"  # Milestone 1 does not yet claim a calibrated severity score


@dataclass
class StructuralEvidence:
    dependency: Dependency
    rule_id: Optional[str]

    def to_dict(self) -> dict:
        return {
            "dependency": self.dependency.to_dict(),
            "rule_id": self.rule_id,
        }


@dataclass
class Finding:
    id: str
    status: FindingStatus
    source: dict  # {"name": ..., "component": ...}
    target: dict  # {"name": ..., "component": ...}
    expected: str
    observed: str
    rule_id: Optional[str]
    severity: Severity

    # Evidence slots. Only structural_evidence is populated in Milestone 1.
    structural_evidence: Optional[StructuralEvidence] = None
    architectural_intent: Optional[dict] = None
    evolution_evidence: Optional[dict] = None  # filled by EvolutionAnalyzer (Milestone 2+)
    semantic_analysis: Optional[dict] = None  # filled by SemanticAnalyzer (Milestone 4+)
    decision: Optional[dict] = None  # filled once an escalation policy exists (Milestone 5+)

    location: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "source": self.source,
            "target": self.target,
            "expected": self.expected,
            "observed": self.observed,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "location": self.location,
            "structural_evidence": (
                self.structural_evidence.to_dict() if self.structural_evidence else None
            ),
            "architectural_intent": self.architectural_intent,
            "evolution_evidence": self.evolution_evidence,
            "semantic_analysis": self.semantic_analysis,
            "decision": self.decision,
        }
