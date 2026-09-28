"""
Core data models for architectural components.

Design note (see Milestone-1 decisions):
There are two levels of granularity:
  - Level 1: architectural component  (e.g. "service", "repository", "database")
  - Level 2: implementation entity     (e.g. "payment_service.py")

Every implementation entity maps to exactly one architectural component
(for Milestone 1). This mapping is derived from repository structure via
a configurable `component_mapping` (see rules/loader.py), NOT hard-coded
directory names.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ComponentType(str, Enum):
    """Architectural roles a piece of code can play.

    This is intentionally open-ended: any string in the repository's
    component_mapping becomes a valid type. The enum below just lists the
    common ones used by the demo/reference architecture so IDE users get
    autocomplete; unknown types still work fine everywhere (they're
    treated as opaque strings by the engine).
    """

    CONTROLLER = "controller"
    SERVICE = "service"
    REPOSITORY = "repository"
    DATABASE = "database"
    MODEL = "model"
    FRONTEND = "frontend"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Component:
    """A Level-2 implementation entity (a file, for Milestone 1)."""

    id: str  # stable identifier, e.g. "backend/services/payment_service.py"
    name: str  # display name, e.g. "payment_service.py"
    path: str  # path relative to the repository root
    architectural_type: str  # Level-1 role, e.g. "service" (see ComponentType)
    language: str  # e.g. "python"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "architectural_type": self.architectural_type,
            "language": self.language,
        }


class DependencyType(str, Enum):
    IMPORT = "import"  # `import x` / `from x import y` — Milestone 1
    CALL = "call"  # function/method call — later
    INHERITANCE = "inheritance"  # class inheritance — later
    INSTANTIATION = "instantiation"  # object construction — later


@dataclass(frozen=True)
class SourceLocation:
    file: str
    line: int

    def to_dict(self) -> dict:
        return {"file": self.file, "line": self.line}


@dataclass(frozen=True)
class Dependency:
    """A single observed edge between two implementation entities."""

    source: str  # Component.id
    target: str  # Component.id
    source_component: str  # architectural type of source
    target_component: str  # architectural type of target
    dependency_type: DependencyType
    location: SourceLocation
    raw_reference: str = ""  # e.g. the literal module path that was imported

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "source_component": self.source_component,
            "target_component": self.target_component,
            "type": self.dependency_type.value,
            "location": self.location.to_dict(),
            "raw_reference": self.raw_reference,
        }
