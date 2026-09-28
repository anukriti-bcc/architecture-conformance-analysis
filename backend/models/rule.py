from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RelationType(str, Enum):
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"
    # Reserved for later milestones — accepted by the schema now so rule
    # files don't need to be rewritten when these are implemented, but the
    # conformance engine currently only acts on ALLOWED / FORBIDDEN.
    REQUIRED = "required"
    CONDITIONAL = "conditional"


@dataclass(frozen=True)
class ArchitectureRule:
    """One explicit architectural constraint, e.g.

    'service' components must NOT depend on 'database' components.
    """

    id: str
    name: str
    source: str  # architectural component type
    target: str  # architectural component type
    relation: RelationType
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value,
            "description": self.description,
        }


@dataclass(frozen=True)
class Architecture:
    """A named set of rules loaded from an architecture/*.yaml file."""

    name: str
    rules: tuple[ArchitectureRule, ...]

    def rules_for(self, source_type: str, target_type: str) -> list[ArchitectureRule]:
        return [
            r for r in self.rules if r.source == source_type and r.target == target_type
        ]
