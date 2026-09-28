from analysis.conformance.engine import analyze_conformance
from models.finding import FindingStatus


def _finding_for(findings, source_suffix, target_suffix):
    return next(
        f
        for f in findings
        if f.source["id"].endswith(source_suffix) and f.target["id"].endswith(target_suffix)
    )


def test_valid_controller_service_is_conformant(scan_result, architecture):
    findings = analyze_conformance(
        scan_result.components, scan_result.dependencies, architecture
    )
    f = _finding_for(findings, "controllers/user_controller.py", "services/user_service.py")
    assert f.status == FindingStatus.CONFORMANT
    assert f.rule_id == "R001"


def test_valid_repository_database_is_conformant(scan_result, architecture):
    findings = analyze_conformance(
        scan_result.components, scan_result.dependencies, architecture
    )
    f = _finding_for(findings, "repositories/user_repository.py", "database/connection.py")
    assert f.status == FindingStatus.CONFORMANT
    assert f.rule_id == "R003"


def test_invalid_service_database_dependency_is_a_violation(scan_result, architecture):
    findings = analyze_conformance(
        scan_result.components, scan_result.dependencies, architecture
    )
    f = _finding_for(findings, "services/payment_service.py", "database/connection.py")
    assert f.status == FindingStatus.VIOLATION
    assert f.rule_id == "R004"
    assert f.severity.value == "high"


def test_violation_carries_structural_evidence_with_correct_line(scan_result, architecture):
    findings = analyze_conformance(
        scan_result.components, scan_result.dependencies, architecture
    )
    f = _finding_for(findings, "services/payment_service.py", "database/connection.py")
    assert f.structural_evidence is not None
    assert f.structural_evidence.dependency.location.line == 45


def test_findings_count_matches_dependency_count(scan_result, architecture):
    findings = analyze_conformance(
        scan_result.components, scan_result.dependencies, architecture
    )
    # Every dependency in the demo repo is governed by some rule (allowed
    # or forbidden), so every dependency should produce exactly one Finding.
    assert len(findings) == len(scan_result.dependencies)


def test_exactly_one_violation_in_demo_repo(scan_result, architecture):
    findings = analyze_conformance(
        scan_result.components, scan_result.dependencies, architecture
    )
    violations = [f for f in findings if f.status == FindingStatus.VIOLATION]
    assert len(violations) == 1
    assert violations[0].source["id"].endswith("payment_service.py")


def test_unspecified_component_pair_is_not_flagged():
    from models.component import Component, Dependency, DependencyType, SourceLocation
    from models.rule import Architecture, ArchitectureRule, RelationType

    # A pair with no rule at all (e.g. "model" -> "model") should not
    # produce a Finding — Milestone 1 does not guess.
    arch = Architecture(
        name="test",
        rules=(
            ArchitectureRule(
                id="R1", name="x", source="controller", target="service",
                relation=RelationType.ALLOWED,
            ),
        ),
    )
    comp_a = Component(id="a.py", name="a.py", path="a.py", architectural_type="model", language="python")
    comp_b = Component(id="b.py", name="b.py", path="b.py", architectural_type="model", language="python")
    dep = Dependency(
        source="a.py", target="b.py",
        source_component="model", target_component="model",
        dependency_type=DependencyType.IMPORT,
        location=SourceLocation(file="a.py", line=1),
    )
    findings = analyze_conformance([comp_a, comp_b], [dep], arch)
    assert findings == []
