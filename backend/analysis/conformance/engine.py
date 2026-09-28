"""
The conformance engine, per currentplan.docx §10:

    FOR every observed dependency:
        identify source component
        identify target component
        find applicable architecture rules
        IF dependency violates a rule:
            create Finding
        ELSE:
            mark as conformant

Deliberately boring and deterministic — no LLM, no learned model. This is
the M1 baseline (see Major_Project_Direction_Working_Brief.docx §9); it
stays in the system permanently as the cheap first pass that later
milestones only escalate away from when evidence is ambiguous.
"""
from __future__ import annotations

from models.component import Component, Dependency
from models.finding import Finding, FindingStatus, Severity, StructuralEvidence
from models.rule import Architecture, RelationType


def _severity_for(relation: RelationType) -> Severity:
    # Milestone 1 does not have a calibrated severity model yet (see
    # Major_Project_Direction_Working_Brief.docx §13 — "should not be
    # included unless formally defined and validated"). We surface a
    # single flat severity for forbidden violations so the UI has
    # something to show, but this is explicitly provisional.
    if relation == RelationType.FORBIDDEN:
        return Severity.HIGH
    return Severity.UNSET


def analyze_conformance(
    components: list[Component],
    dependencies: list[Dependency],
    architecture: Architecture,
) -> list[Finding]:
    components_by_id = {c.id: c for c in components}
    findings: list[Finding] = []

    for i, dep in enumerate(dependencies):
        applicable_rules = architecture.rules_for(dep.source_component, dep.target_component)

        source_component = components_by_id.get(dep.source)
        target_component = components_by_id.get(dep.target)

        # No explicit rule governs this source/target component pair at
        # all: Milestone 1 does not flag it either way (it's neither
        # confirmed conformant nor a violation — an "unspecified"
        # relationship). This avoids false positives on architecture
        # files that don't enumerate every legal relationship.
        forbidding_rule = next(
            (r for r in applicable_rules if r.relation == RelationType.FORBIDDEN), None
        )
        allowing_rule = next(
            (r for r in applicable_rules if r.relation == RelationType.ALLOWED), None
        )

        if forbidding_rule is None and allowing_rule is None:
            continue

        status = FindingStatus.VIOLATION if forbidding_rule else FindingStatus.CONFORMANT
        matched_rule = forbidding_rule or allowing_rule

        expected = (
            f"{dep.source_component} must not depend directly on {dep.target_component}"
            if forbidding_rule
            else f"{dep.source_component} may depend on {dep.target_component}"
        )
        observed = f"{dep.source_component} depends directly on {dep.target_component}"

        finding = Finding(
            id=f"F{i + 1:03d}",
            status=status,
            source={
                "name": source_component.name if source_component else dep.source,
                "component": dep.source_component,
                "id": dep.source,
            },
            target={
                "name": target_component.name if target_component else dep.target,
                "component": dep.target_component,
                "id": dep.target,
            },
            expected=expected,
            observed=observed,
            rule_id=matched_rule.id if matched_rule else None,
            severity=_severity_for(matched_rule.relation) if matched_rule else Severity.UNSET,
            structural_evidence=StructuralEvidence(
                dependency=dep, rule_id=matched_rule.id if matched_rule else None
            ),
            location=dep.location.to_dict(),
        )
        findings.append(finding)

    return findings
