"""
Ties together the parser layer, the module index, and the component
mapping to turn a repository on disk into:
  - a list of Component objects (Level-2 implementation entities)
  - a list of Dependency objects (Level-1 architectural edges, with
    Level-2 source-location evidence attached)

This is the one place that touches the filesystem directly; everything
downstream (graph builder, conformance engine) works purely on the
in-memory Component/Dependency objects, so it doesn't matter whether they
came from disk, a Git checkout, or (later) a language server.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from analysis.dependency.module_index import ModuleIndex
from analysis.parser.registry import get_parser_for_file, supported_extensions
from models.component import Component, Dependency, DependencyType, SourceLocation
from rules.loader import ComponentMapping

_IGNORED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".pytest_cache",
    "dist",
    "build",
    ".mypy_cache",
    "architecture",  # rules live here, not source
    # Test code deliberately breaks layering on purpose (test doubles,
    # fixtures reaching into repositories/databases directly) — that's
    # correct test-engineering practice, not architectural drift. Found
    # via real-world validation against a third-party repo (see
    # docs/STUDY_GUIDE.md §"generalization test"): without this, test
    # helper files were flagged as false-positive violations. Milestone 1
    # scores production architecture, not test code.
    "test",
    "tests",
    "__tests__",
    "spec",
    "specs",
}


@dataclass
class ScanResult:
    components: list[Component]
    dependencies: list[Dependency]
    external_imports: list[str]  # imports that couldn't be resolved inside the repo


def _relative_path(root: str, full_path: str) -> str:
    return os.path.relpath(full_path, root).replace(os.sep, "/")


def _architectural_type_for(
    relative_path: str, mapping: ComponentMapping
) -> str:
    """Walk the path's directories from deepest to shallowest and use the
    first one that appears in the component_mapping — i.e. the *closest*
    matching ancestor directory wins (most specific)."""
    dir_parts = relative_path.split("/")[:-1]
    for part in reversed(dir_parts):
        component_type = mapping.type_for_directory(part)
        if component_type is not None:
            return component_type
    return "unknown"


def _collect_source_files(root: str) -> list[str]:
    """Returns every source file under `root`, in a stable, OS-independent
    order (sorted by path relative to `root`).

    `os.walk` does NOT guarantee a consistent traversal order across
    filesystems/operating systems (NTFS and ext4, for instance, can yield
    files in different sequences for the identical directory tree). Since
    Finding IDs are assigned by the order dependencies are discovered,
    an unsorted walk means the *same* repository could produce different
    Finding IDs on different machines — a real reproducibility bug, not
    just a cosmetic one. Sorting here makes a scan of a given repository
    produce byte-for-byte identical output regardless of OS/filesystem.
    """
    exts = supported_extensions()
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in _IGNORED_DIRS and not d.startswith(".")
        )
        for fname in sorted(filenames):
            if fname.endswith(exts):
                files.append(os.path.join(dirpath, fname))
    return sorted(files, key=lambda p: _relative_path(root, p))


def scan_repository(root: str, component_mapping: ComponentMapping) -> ScanResult:
    root = os.path.abspath(root)
    source_files = _collect_source_files(root)

    # Pass 1: build the module index and the Component objects.
    index = ModuleIndex()
    components: dict[str, Component] = {}
    for full_path in source_files:
        rel = _relative_path(root, full_path)
        index.add_file(rel)
        arch_type = _architectural_type_for(rel, component_mapping)
        components[rel] = Component(
            id=rel,
            name=os.path.basename(rel),
            path=rel,
            architectural_type=arch_type,
            language="python",  # Milestone 1: Python only
        )

    # Pass 2: parse each file and resolve its imports into Dependency edges.
    dependencies: list[Dependency] = []
    external_imports: list[str] = []

    for full_path in source_files:
        rel = _relative_path(root, full_path)
        parser = get_parser_for_file(rel)
        if parser is None:
            continue

        with open(full_path, "rb") as f:
            source = f.read()

        tree = parser.parse(source)
        raw_imports = parser.extract_imports(tree, source)
        source_component = components[rel]

        for raw in raw_imports:
            target_rel = None
            if raw.is_relative:
                if raw.imported_names:
                    # `from . import database` / `from .models import User`
                    # — try resolving each imported name as a submodule first
                    # (e.g. `.database` -> database.py), since that's the
                    # common layered-architecture pattern this tool targets.
                    for name in raw.imported_names:
                        target_rel = index.resolve_relative_name(rel, raw.module, name)
                        if target_rel:
                            break
                if target_rel is None:
                    target_rel = index.resolve_relative(rel, raw.module)
            else:
                target_rel = index.resolve_absolute(raw.module)
                if target_rel is None and raw.imported_names:
                    # `from services import payment_service` style — module
                    # itself might be a package; try module.name as a file.
                    for name in raw.imported_names:
                        candidate = index.resolve_absolute(f"{raw.module}.{name}")
                        if candidate:
                            target_rel = candidate
                            break

            if target_rel is None or target_rel == rel:
                if not raw.is_relative:
                    external_imports.append(raw.module)
                continue

            target_component = components[target_rel]
            dependencies.append(
                Dependency(
                    source=rel,
                    target=target_rel,
                    source_component=source_component.architectural_type,
                    target_component=target_component.architectural_type,
                    dependency_type=DependencyType.IMPORT,
                    location=SourceLocation(file=rel, line=raw.line),
                    raw_reference=raw.module
                    + (f".{raw.imported_names[0]}" if raw.imported_names else ""),
                )
            )

    return ScanResult(
        components=list(components.values()),
        dependencies=dependencies,
        external_imports=sorted(set(external_imports)),
    )
