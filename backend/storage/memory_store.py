"""
In-memory storage for analysis runs.

currentplan.docx lists PostgreSQL as the eventual database, storing
repositories/components/dependencies/rules/findings/commits/evidence
long-term. That's not on the critical path for the mid-viva demo, so
Milestone 1 keeps analysis runs in memory behind this one module. If/when
persistence is added, only this file needs to change — the API layer
already treats it as a black box with get/save/list.
"""
from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import networkx as nx

from models.finding import Finding
from models.component import Component, Dependency
from models.rule import Architecture


@dataclass
class AnalysisRun:
    id: str
    repository_path: str
    architecture_name: str
    created_at: str
    components: list[Component]
    dependencies: list[Dependency]
    architecture: Architecture
    findings: list[Finding]
    graph: nx.DiGraph
    external_imports: list[str]

    def summary(self) -> dict:
        violations = [f for f in self.findings if f.status.value == "violation"]
        return {
            "analysis_id": self.id,
            "repository": self.repository_path,
            "architecture": self.architecture_name,
            "created_at": self.created_at,
            "components": len(self.components),
            "dependencies": len(self.dependencies),
            "rules": len(self.architecture.rules),
            "findings": len(self.findings),
            "violations": len(violations),
        }


class _MemoryStore:
    def __init__(self) -> None:
        self._runs: dict[str, AnalysisRun] = {}
        self._findings_by_id: dict[str, Finding] = {}
        self._counter = itertools.count(1)
        self._lock = threading.Lock()

    def next_id(self) -> str:
        with self._lock:
            n = next(self._counter)
        return f"A{n:04d}"

    def save(self, run: AnalysisRun) -> None:
        self._runs[run.id] = run
        for finding in run.findings:
            self._findings_by_id[finding.id] = finding

    def get(self, analysis_id: str) -> AnalysisRun | None:
        return self._runs.get(analysis_id)

    def list_all(self) -> list[AnalysisRun]:
        return list(self._runs.values())

    def get_finding(self, finding_id: str) -> Finding | None:
        return self._findings_by_id.get(finding_id)


store = _MemoryStore()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
