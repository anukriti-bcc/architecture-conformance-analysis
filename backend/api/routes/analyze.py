from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from analysis.conformance.engine import analyze_conformance
from analysis.dependency.graph import build_dependency_graph, graph_to_dict
from analysis.dependency.repository_scanner import scan_repository
from analysis.evolution.base import NotYetImplementedEvolutionAnalyzer
from analysis.semantic.base import NotYetImplementedSemanticAnalyzer
from api.schemas.analyze import (
    AnalysisSummary,
    AnalyzeRequest,
    AnalyzeResponse,
    FindingDetail,
    FindingSummary,
    GraphResponse,
)
from models.rule import RelationType
from rules.loader import ArchitectureFileError, load_architecture_file
from storage.memory_store import AnalysisRun, now_iso, store

router = APIRouter()

_evolution_analyzer = NotYetImplementedEvolutionAnalyzer()
_semantic_analyzer = NotYetImplementedSemanticAnalyzer()


@router.post("/repositories/analyze", response_model=AnalyzeResponse)
def analyze_repository(request: AnalyzeRequest) -> AnalyzeResponse:
    if not os.path.isdir(request.repository_path):
        raise HTTPException(
            status_code=400, detail=f"repository_path '{request.repository_path}' does not exist."
        )
    if not os.path.isfile(request.architecture_file):
        raise HTTPException(
            status_code=400,
            detail=f"architecture_file '{request.architecture_file}' does not exist.",
        )

    try:
        architecture, mapping = load_architecture_file(request.architecture_file)
    except ArchitectureFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    scan_result = scan_repository(request.repository_path, mapping)
    graph = build_dependency_graph(scan_result.components, scan_result.dependencies)
    findings = analyze_conformance(scan_result.components, scan_result.dependencies, architecture)

    run = AnalysisRun(
        id=store.next_id(),
        repository_path=request.repository_path,
        architecture_name=architecture.name,
        created_at=now_iso(),
        components=scan_result.components,
        dependencies=scan_result.dependencies,
        architecture=architecture,
        findings=findings,
        graph=graph,
        external_imports=scan_result.external_imports,
    )
    store.save(run)

    return AnalyzeResponse(
        analysis_id=run.id,
        repository=run.repository_path,
        architecture=run.architecture_name,
        created_at=run.created_at,
        components=len(run.components),
        dependencies=len(run.dependencies),
        rules=len(run.architecture.rules),
        findings=[
            FindingSummary(
                id=f.id,
                status=f.status.value,
                source=f.source,
                target=f.target,
                rule_id=f.rule_id,
                severity=f.severity.value,
            )
            for f in run.findings
        ],
        external_imports=run.external_imports,
    )


@router.get("/analysis", response_model=list[AnalysisSummary])
def list_analyses() -> list[AnalysisSummary]:
    return [AnalysisSummary(**run.summary()) for run in store.list_all()]


@router.get("/analysis/{analysis_id}", response_model=AnalysisSummary)
def get_analysis(analysis_id: str) -> AnalysisSummary:
    run = store.get(analysis_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    return AnalysisSummary(**run.summary())


@router.get("/analysis/{analysis_id}/graph", response_model=GraphResponse)
def get_analysis_graph(analysis_id: str) -> GraphResponse:
    run = store.get(analysis_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")

    violation_edges = {
        (f.structural_evidence.dependency.source, f.structural_evidence.dependency.target)
        for f in run.findings
        if f.status.value == "violation" and f.structural_evidence
    }
    return GraphResponse(**graph_to_dict(run.graph, violation_edges))


@router.get("/analysis/{analysis_id}/findings", response_model=list[FindingSummary])
def get_analysis_findings(analysis_id: str) -> list[FindingSummary]:
    run = store.get(analysis_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    return [
        FindingSummary(
            id=f.id,
            status=f.status.value,
            source=f.source,
            target=f.target,
            rule_id=f.rule_id,
            severity=f.severity.value,
        )
        for f in run.findings
    ]


@router.get("/findings/{finding_id}", response_model=FindingDetail)
def get_finding(finding_id: str) -> FindingDetail:
    finding = store.get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found.")
    return FindingDetail(**finding.to_dict())


@router.get("/findings/{finding_id}/evolution")
def get_finding_evolution(finding_id: str) -> dict:
    """Milestone 2 boundary. Returns null evidence today — see
    analysis/evolution/base.py. Kept as a real endpoint (not a 404) so
    the frontend can call it unconditionally and just render "not yet
    analyzed" when the payload is empty.
    """
    finding = store.get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found.")
    evidence = _evolution_analyzer.analyze(repository_path="", finding=finding)
    return {"finding_id": finding_id, "evolution_evidence": evidence}


@router.post("/findings/{finding_id}/semantic-analysis")
def request_semantic_analysis(finding_id: str) -> dict:
    """Milestone 4 boundary — intentionally not implemented yet (see
    analysis/semantic/base.py and currentplan.docx: "we risk building the
    wrong thing" if this is hard-coded before the escalation policy and
    model are decided). Returns 501 rather than a fake result.
    """
    finding = store.get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"Finding '{finding_id}' not found.")
    raise HTTPException(
        status_code=501,
        detail=(
            "Semantic analysis is not implemented yet. This endpoint is the "
            "designed boundary for the future LLM-based SemanticAnalyzer "
            "(Milestone 4)."
        ),
    )
