"""
Resolves a dotted Python module path (as literally written in an import
statement) to a file inside the repository.

Known Milestone-1 simplification (documented, not hidden): we don't
execute or introspect `sys.path`, so we resolve a module by matching it
against every *suffix* of each file's dotted path. This works well for
the common layered-architecture layout this project targets
(controllers/services/repositories/...), and for the demo/reference
repositories. It can misresolve in repos with duplicate module basenames
across unrelated packages — a documented limitation, not a silent one,
and it is isolated entirely inside this module so it can be swapped for
a proper import-resolution algorithm later without touching the parser,
conformance engine, or API.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def _dotted_suffixes(dir_parts: list[str], stem: str) -> list[str]:
    """All dotted-path suffixes of a file, longest first.

    e.g. dir_parts=["backend","services"], stem="payment_service" ->
    ["backend.services.payment_service", "services.payment_service", "payment_service"]
    """
    parts = [*dir_parts, stem] if stem else list(dir_parts)
    return [".".join(parts[i:]) for i in range(len(parts))]


@dataclass
class ModuleIndex:
    """Maps dotted module suffixes -> list of candidate file paths (relative
    to repo root), and file directory -> file paths (for relative-import
    resolution)."""

    _suffix_to_paths: dict[str, list[str]] = field(default_factory=dict)
    _dir_listing: dict[str, list[str]] = field(default_factory=dict)  # dir -> [stems]

    def add_file(self, relative_path: str) -> None:
        relative_path = relative_path.replace("\\", "/")
        dir_path, filename = relative_path.rsplit("/", 1) if "/" in relative_path else (
            "",
            relative_path,
        )
        dir_parts = [p for p in dir_path.split("/") if p]

        if filename == "__init__.py":
            stem = ""
        else:
            stem = filename[:-3] if filename.endswith(".py") else filename

        for suffix in _dotted_suffixes(dir_parts, stem):
            self._suffix_to_paths.setdefault(suffix, [])
            if relative_path not in self._suffix_to_paths[suffix]:
                self._suffix_to_paths[suffix].append(relative_path)

        self._dir_listing.setdefault(dir_path, [])
        if relative_path not in self._dir_listing[dir_path]:
            self._dir_listing[dir_path].append(relative_path)

    def resolve_absolute(self, module: str) -> str | None:
        """Resolve a non-relative dotted module path, e.g. 'services.payment'."""
        candidates = self._suffix_to_paths.get(module)
        if not candidates:
            return None
        # Prefer the candidate whose full dotted path most closely matches
        # (i.e. the fewest leading path segments were dropped) — this is
        # the "closest, most specific" match.
        return min(candidates, key=len)

    def resolve_relative(
        self, importing_file: str, relative_module: str
    ) -> str | None:
        """Resolve a relative import ('.', '.models', '..shared') relative
        to the file that contains the import statement."""
        dir_path = (
            importing_file.rsplit("/", 1)[0] if "/" in importing_file else ""
        )
        dir_parts = [p for p in dir_path.split("/") if p]

        dots = 0
        while dots < len(relative_module) and relative_module[dots] == ".":
            dots += 1
        remainder = relative_module[dots:]

        # one dot = current package; each extra dot goes up one more level
        levels_up = dots - 1
        base_parts = dir_parts[: len(dir_parts) - levels_up] if levels_up > 0 else dir_parts
        if remainder:
            module = ".".join([*base_parts, remainder]) if base_parts else remainder
        else:
            module = ".".join(base_parts)

        return self.resolve_absolute(module) if module else None

    def resolve_relative_name(
        self, importing_file: str, relative_module: str, name: str
    ) -> str | None:
        """For `from . import database` — `database` might itself be a
        submodule (database.py) rather than an attribute of the package.
        Try resolving `<relative_module>.<name>` as a module path first.
        """
        dir_path = (
            importing_file.rsplit("/", 1)[0] if "/" in importing_file else ""
        )
        dir_parts = [p for p in dir_path.split("/") if p]
        dots = 0
        while dots < len(relative_module) and relative_module[dots] == ".":
            dots += 1
        remainder = relative_module[dots:]
        levels_up = dots - 1
        base_parts = dir_parts[: len(dir_parts) - levels_up] if levels_up > 0 else dir_parts
        full_parts = [*base_parts, remainder, name] if remainder else [*base_parts, name]
        module = ".".join(p for p in full_parts if p)
        return self.resolve_absolute(module)
