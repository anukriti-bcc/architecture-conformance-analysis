import pytest

from rules.loader import ArchitectureFileError, load_architecture_file


def test_loads_architecture_name(architecture):
    assert architecture.name == "layered-architecture"


def test_loads_all_rules(architecture):
    assert len(architecture.rules) == 7
    ids = {r.id for r in architecture.rules}
    assert "R004" in ids  # no-service-database


def test_loads_component_mapping(component_mapping):
    assert component_mapping.type_for_directory("services") == "service"
    assert component_mapping.type_for_directory("database") == "database"
    assert component_mapping.type_for_directory("nonexistent") is None


def test_rules_for_returns_matching_rules(architecture):
    forbidden = architecture.rules_for("service", "database")
    assert len(forbidden) == 1
    assert forbidden[0].relation.value == "forbidden"


def test_rejects_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    with pytest.raises(FileNotFoundError):
        load_architecture_file(str(missing))


def test_rejects_rule_missing_required_field(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        "architecture:\n  name: test\nrules:\n  - id: R1\n    source: a\n    target: b\n"
        # missing 'relation'
    )
    with pytest.raises(ArchitectureFileError):
        load_architecture_file(str(bad_yaml))


def test_rejects_unknown_relation(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        "architecture:\n  name: test\nrules:\n"
        "  - id: R1\n    source: a\n    target: b\n    relation: maybe\n"
    )
    with pytest.raises(ArchitectureFileError):
        load_architecture_file(str(bad_yaml))
