import os

import pytest
from fastapi.testclient import TestClient

from main import app

REPO_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "datasets",
    "sample-ecommerce",
)
ARCH_FILE = os.path.join(REPO_ROOT, "architecture", "rules.yaml")


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def analysis_id(client):
    resp = client.post(
        "/repositories/analyze",
        json={"repository_path": REPO_ROOT, "architecture_file": ARCH_FILE},
    )
    assert resp.status_code == 200
    return resp.json()["analysis_id"]


def test_analyze_returns_200_and_findings(client):
    resp = client.post(
        "/repositories/analyze",
        json={"repository_path": REPO_ROOT, "architecture_file": ARCH_FILE},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["components"] == 12
    assert data["dependencies"] == 7
    violations = [f for f in data["findings"] if f["status"] == "violation"]
    assert len(violations) == 1


def test_analyze_rejects_missing_repo(client):
    resp = client.post(
        "/repositories/analyze",
        json={"repository_path": "/nonexistent/path", "architecture_file": ARCH_FILE},
    )
    assert resp.status_code == 400


def test_get_analysis_graph(client, analysis_id):
    resp = client.get(f"/analysis/{analysis_id}/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) == 12
    assert len(data["edges"]) == 7
    violation_edges = [e for e in data["edges"] if e["is_violation"]]
    assert len(violation_edges) == 1


@pytest.fixture
def violation_finding_id(client, analysis_id):
    """Looks up the violation's Finding ID by content rather than assuming
    a fixed ID like 'F004' — Finding IDs are assigned by discovery order,
    which is now stable *within* a single scan (see repository_scanner.py's
    sorted _collect_source_files), but tests shouldn't hardcode a specific
    number regardless, since it's an implementation detail, not a contract."""
    findings = client.get(f"/analysis/{analysis_id}/findings").json()
    violation = next(f for f in findings if f["status"] == "violation")
    return violation["id"]


def test_get_finding_detail(client, violation_finding_id):
    resp = client.get(f"/findings/{violation_finding_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "violation"
    assert data["structural_evidence"] is not None
    assert data["evolution_evidence"] is None
    assert data["semantic_analysis"] is None


def test_finding_not_found(client, analysis_id):
    resp = client.get("/findings/F999")
    assert resp.status_code == 404


def test_semantic_analysis_endpoint_returns_501(client, violation_finding_id):
    resp = client.post(f"/findings/{violation_finding_id}/semantic-analysis")
    assert resp.status_code == 501


def test_evolution_endpoint_returns_null_evidence(client, violation_finding_id):
    resp = client.get(f"/findings/{violation_finding_id}/evolution")
    assert resp.status_code == 200
    assert resp.json()["evolution_evidence"] is None
