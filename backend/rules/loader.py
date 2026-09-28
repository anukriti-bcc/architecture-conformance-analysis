"""
Loads an architecture definition file (YAML) into:
  - a ComponentMapping: directory-name -> architectural_type
  - an Architecture: named set of ArchitectureRule

Expected schema (see rules/schema_example.yaml and
datasets/sample-ecommerce/architecture/rules.yaml for worked examples):

architecture:
  name: layered-architecture

component_mapping:
  controllers:
    type: controller
  services:
    type: service
  repositories:
    type: repository
  database:
    type: database

rules:
  - id: R001
    name: controller-service
    source: controller
    target: service
    relation: allowed
  - id: R003
    name: service-database
    source: service
    target: database
    relation: forbidden

This is intentionally simple (see currentplan.docx §6-7): only
allowed/forbidden relations are acted on for Milestone 1. `required` and
`conditional` are accepted by the schema (so files don't need rewriting
later) but the conformance engine does not yet implement them.
"""
from __future__ import annotations

from dataclasses import dataclass

import yaml

from models.rule import Architecture, ArchitectureRule, RelationType


class ArchitectureFileError(ValueError):
    """Raised when an architecture YAML file is missing required fields."""


@dataclass(frozen=True)
class ComponentMapping:
    """Maps a top-level (or nested) directory name to an architectural type.

    e.g. {"controllers": "controller", "services": "service", ...}
    """

    mapping: dict[str, str]

    def type_for_directory(self, directory_name: str) -> str | None:
        return self.mapping.get(directory_name)


def load_architecture_file(path: str) -> tuple[Architecture, ComponentMapping]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw:
        raise ArchitectureFileError(f"Architecture file '{path}' is empty.")

    arch_meta = raw.get("architecture") or {}
    name = arch_meta.get("name", "unnamed-architecture")

    raw_mapping = raw.get("component_mapping") or {}
    mapping: dict[str, str] = {}
    for dir_name, cfg in raw_mapping.items():
        if not isinstance(cfg, dict) or "type" not in cfg:
            raise ArchitectureFileError(
                f"component_mapping entry '{dir_name}' must have a 'type' field."
            )
        mapping[dir_name] = cfg["type"]

    raw_rules = raw.get("rules") or []
    rules: list[ArchitectureRule] = []
    for r in raw_rules:
        for field_name in ("id", "source", "target", "relation"):
            if field_name not in r:
                raise ArchitectureFileError(
                    f"Rule {r} is missing required field '{field_name}'."
                )
        try:
            relation = RelationType(r["relation"])
        except ValueError as exc:
            raise ArchitectureFileError(
                f"Rule {r['id']} has unknown relation '{r['relation']}'."
            ) from exc
        rules.append(
            ArchitectureRule(
                id=r["id"],
                name=r.get("name", r["id"]),
                source=r["source"],
                target=r["target"],
                relation=relation,
                description=r.get("description", ""),
            )
        )

    return Architecture(name=name, rules=tuple(rules)), ComponentMapping(mapping=mapping)
