import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rules.loader import load_architecture_file
from analysis.dependency.repository_scanner import scan_repository

REPO_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "datasets",
    "sample-ecommerce",
)
ARCH_FILE = os.path.join(REPO_ROOT, "architecture", "rules.yaml")


@pytest.fixture(scope="session")
def architecture():
    arch, _mapping = load_architecture_file(ARCH_FILE)
    return arch


@pytest.fixture(scope="session")
def component_mapping():
    _arch, mapping = load_architecture_file(ARCH_FILE)
    return mapping


@pytest.fixture(scope="session")
def scan_result(component_mapping):
    return scan_repository(REPO_ROOT, component_mapping)
