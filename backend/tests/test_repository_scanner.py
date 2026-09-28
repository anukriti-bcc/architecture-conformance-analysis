def _dep_exists(dependencies, source_suffix, target_suffix):
    return any(
        d.source.endswith(source_suffix) and d.target.endswith(target_suffix)
        for d in dependencies
    )


def test_maps_directory_to_component(scan_result):
    types = {c.path: c.architectural_type for c in scan_result.components}
    assert types["backend/controllers/user_controller.py"] == "controller"
    assert types["backend/services/user_service.py"] == "service"
    assert types["backend/repositories/user_repository.py"] == "repository"
    assert types["backend/database/connection.py"] == "database"


def test_finds_all_source_files(scan_result):
    # 2 controllers, 2 services, 2 repositories, 1 database module,
    # plus 5 __init__.py files (backend + 4 subpackages)
    assert len(scan_result.components) == 12


def test_valid_controller_service_dependency(scan_result):
    assert _dep_exists(
        scan_result.dependencies,
        "controllers/user_controller.py",
        "services/user_service.py",
    )


def test_valid_service_repository_dependency(scan_result):
    assert _dep_exists(
        scan_result.dependencies,
        "services/user_service.py",
        "repositories/user_repository.py",
    )


def test_valid_repository_database_dependency(scan_result):
    assert _dep_exists(
        scan_result.dependencies,
        "repositories/user_repository.py",
        "database/connection.py",
    )


def test_detects_the_deliberate_service_database_violation(scan_result):
    assert _dep_exists(
        scan_result.dependencies,
        "services/payment_service.py",
        "database/connection.py",
    )


def test_detects_import_location(scan_result):
    dep = next(
        d
        for d in scan_result.dependencies
        if d.source.endswith("payment_service.py") and d.target.endswith("connection.py")
    )
    assert dep.location.line == 45
    assert dep.location.file.endswith("payment_service.py")


def test_ignores_external_dependencies(scan_result):
    # No stdlib/third-party imports appear in the demo repo's Python files,
    # so nothing should show up as unresolved/external.
    assert scan_result.external_imports == []


def test_test_directories_are_excluded_from_scanning(tmp_path, component_mapping):
    """Test code deliberately breaks layering on purpose (fixtures reaching
    into repositories directly) — that's correct test-engineering practice,
    not architectural drift, and should never produce a Finding. Regression
    test for a false positive found via real-world validation (see
    docs/STUDY_GUIDE.md) against github.com/serfer2/flask-hexagonal-architecture-api."""
    from analysis.dependency.repository_scanner import scan_repository

    repo = tmp_path / "repo"
    (repo / "controllers").mkdir(parents=True)
    (repo / "database").mkdir()
    (repo / "test" / "controllers").mkdir(parents=True)

    (repo / "controllers" / "__init__.py").write_text("")
    (repo / "database" / "__init__.py").write_text("")
    (repo / "database" / "connection.py").write_text("")
    (repo / "test" / "__init__.py").write_text("")
    (repo / "test" / "controllers" / "__init__.py").write_text("")
    (repo / "test" / "controllers" / "test_something.py").write_text(
        "from database.connection import get_connection\n"
    )

    result = scan_repository(str(repo), component_mapping)
    paths = [c.path for c in result.components]
    assert not any(p.startswith("test/") for p in paths)
    assert not any(d.source.startswith("test/") for d in result.dependencies)


def test_scan_order_is_deterministic(component_mapping):
    """Regression test: os.walk() does not guarantee a consistent file
    order across filesystems/operating systems, and Finding IDs are
    assigned by discovery order — so an unsorted scan could produce
    different Finding IDs for the identical repository on different
    machines. Runs the scan twice and checks the component and dependency
    order is byte-for-byte identical, proving the fix in
    repository_scanner.py's _collect_source_files actually works."""
    from analysis.dependency.repository_scanner import scan_repository
    import os as _os

    repo_root = _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
        "datasets",
        "sample-ecommerce",
    )
    result_a = scan_repository(repo_root, component_mapping)
    result_b = scan_repository(repo_root, component_mapping)

    assert [c.id for c in result_a.components] == [c.id for c in result_b.components]
    assert [(d.source, d.target) for d in result_a.dependencies] == [
        (d.source, d.target) for d in result_b.dependencies
    ]


def test_relative_import_resolves_correctly(scan_result):
    # payment_service.py does `from backend.repositories.payment_repository
    # import PaymentRepository` (absolute-style within-repo import) —
    # confirm it resolves rather than being dropped as external.
    assert _dep_exists(
        scan_result.dependencies,
        "services/payment_service.py",
        "repositories/payment_repository.py",
    )
