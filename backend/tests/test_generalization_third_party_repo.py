"""
Generalization test — proves the engine isn't hard-coded against the
bundled demo repo.

Runs the unmodified scanner + conformance engine against a real,
unrelated, third-party GitHub project this codebase has never seen:
github.com/serfer2/flask-hexagonal-architecture-api (hexagonal/ports-
and-adapters Flask API — controller / application-services / domain /
infrastructure layers).

This test is SKIPPED if the fixture repo isn't present locally (it's not
committed to this repo — clone it yourself to re-run this test):

    git clone --depth 1 \
        https://github.com/serfer2/flask-hexagonal-architecture-api.git \
        /tmp/flask-hexagonal-architecture-api

    THIRD_PARTY_REPO=/tmp/flask-hexagonal-architecture-api pytest \
        tests/test_generalization_third_party_repo.py -v

See docs/STUDY_GUIDE.md, "generalization test" section, for the full
walkthrough and the reasoning behind the rules.yaml used here.
"""
import os

import pytest
import yaml

from analysis.conformance.engine import analyze_conformance
from analysis.dependency.repository_scanner import scan_repository
from rules.loader import ComponentMapping
from models.rule import Architecture, ArchitectureRule, RelationType

REPO_PATH = os.environ.get(
    "THIRD_PARTY_REPO", "/tmp/flask-hexagonal-architecture-api"
)
SRC_PATH = os.path.join(REPO_PATH, "src")

pytestmark = pytest.mark.skipif(
    not os.path.isdir(SRC_PATH),
    reason=(
        f"Third-party fixture repo not found at {SRC_PATH}. "
        "Clone it to re-run this generalization test (see module docstring)."
    ),
)


@pytest.fixture(scope="module")
def third_party_architecture():
    return (
        Architecture(
            name="hexagonal-architecture-test",
            rules=(
                ArchitectureRule("R001", "controller-service", "controller", "service", RelationType.ALLOWED),
                ArchitectureRule("R002", "service-repository", "service", "repository", RelationType.ALLOWED),
                ArchitectureRule("R003", "repository-database", "repository", "database", RelationType.ALLOWED),
                ArchitectureRule("R004", "no-controller-database", "controller", "database", RelationType.FORBIDDEN),
                ArchitectureRule("R005", "no-controller-repository", "controller", "repository", RelationType.FORBIDDEN),
                ArchitectureRule("R006", "no-service-database", "service", "database", RelationType.FORBIDDEN),
            ),
        ),
        ComponentMapping(
            mapping={
                "controller": "controller",
                "services": "service",
                "repositories": "repository",
                "infrastructure": "database",
                "models": "model",
            }
        ),
    )


def test_extracts_real_components_with_correct_types(third_party_architecture):
    architecture, mapping = third_party_architecture
    result = scan_repository(SRC_PATH, mapping)

    types = {c.path: c.architectural_type for c in result.components}
    assert types["controller/app.py"] == "controller"
    assert types["application/services/acquire_pdf_file.py"] == "service"
    assert types["infrastructure/repositories/report_repository.py"] == "repository"
    assert types["infrastructure/database.py"] == "database"
    assert types["domain/models/report.py"] == "model"


def test_correctly_excludes_third_party_and_stdlib_imports(third_party_architecture):
    architecture, mapping = third_party_architecture
    result = scan_repository(SRC_PATH, mapping)

    for external in ("flask", "sqlalchemy", "hashlib", "os", "re"):
        assert external in result.external_imports


def test_finds_real_conformant_dependency(third_party_architecture):
    architecture, mapping = third_party_architecture
    result = scan_repository(SRC_PATH, mapping)
    findings = analyze_conformance(result.components, result.dependencies, architecture)

    conformant_ids = {
        (f.source["id"], f.target["id"]) for f in findings if f.status.value == "conformant"
    }
    assert ("infrastructure/repositories/report_repository.py", "infrastructure/database.py") in conformant_ids


def test_finds_real_violations_in_unmodified_third_party_code(third_party_architecture):
    """controller/app.py wires the DB connection and repository directly
    into route handlers (a composition-root pattern) — under this
    strict-layering ruleset that's a genuine, reproducible finding in
    code this project's authors never showed us."""
    architecture, mapping = third_party_architecture
    result = scan_repository(SRC_PATH, mapping)
    findings = analyze_conformance(result.components, result.dependencies, architecture)

    violation_ids = {
        (f.source["id"], f.target["id"], f.rule_id)
        for f in findings
        if f.status.value == "violation"
    }
    assert ("controller/app.py", "infrastructure/database.py", "R004") in violation_ids
    assert ("controller/app.py", "infrastructure/repositories/__init__.py", "R005") in violation_ids


def test_no_false_positives_from_test_directory(third_party_architecture):
    architecture, mapping = third_party_architecture
    result = scan_repository(SRC_PATH, mapping)
    assert not any(c.path.startswith("test/") for c in result.components)
