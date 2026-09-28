from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    repository_path: str = Field(
        ..., description="Path to the repository on disk (Milestone 1: local paths only)."
    )
    architecture_file: str = Field(
        ..., description="Path to the architecture YAML file (component_mapping + rules)."
    )


class FindingSummary(BaseModel):
    id: str
    status: str
    source: dict
    target: dict
    rule_id: Optional[str]
    severity: str


class AnalyzeResponse(BaseModel):
    analysis_id: str
    repository: str
    architecture: str
    created_at: str
    components: int
    dependencies: int
    rules: int
    findings: list[FindingSummary]
    external_imports: list[str]


class AnalysisSummary(BaseModel):
    analysis_id: str
    repository: str
    architecture: str
    created_at: str
    components: int
    dependencies: int
    rules: int
    findings: int
    violations: int


class GraphResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class FindingDetail(BaseModel):
    id: str
    status: str
    source: dict
    target: dict
    expected: str
    observed: str
    rule_id: Optional[str]
    severity: str
    location: Optional[dict]
    structural_evidence: Optional[dict]
    architectural_intent: Optional[dict]
    evolution_evidence: Optional[dict]
    semantic_analysis: Optional[dict]
    decision: Optional[dict]
