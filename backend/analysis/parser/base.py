"""
LanguageParser is the abstraction that keeps the conformance engine
language-agnostic. Adding a new language later (JavaScript, TypeScript,
Java, ...) means writing one new subclass here — nothing downstream
(dependency graph, conformance engine, API) needs to change.

Every concrete parser is backed by Tree-sitter (not regex), so the same
grammar-accurate approach scales to new languages without redesigning
this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RawImport:
    """One import statement as literally observed in the source, before
    it is resolved to a Component or checked against any rule."""

    module: str  # dotted/relative module path as written, e.g. "services.payment"
    imported_names: tuple[str, ...]  # names pulled in, e.g. ("PaymentService",)
    line: int
    is_relative: bool = False


class LanguageParser(ABC):
    """Interface every per-language parser must implement.

    Concrete implementations parse a single source file (already read
    into memory) and return the raw import statements found in it. They
    deliberately do NOT resolve those imports to filesystem paths or
    architectural components — that is the RepositoryParser's job, so
    the same resolution logic works across languages.
    """

    #: file extensions this parser claims, e.g. (".py",)
    extensions: tuple[str, ...] = ()

    @abstractmethod
    def parse(self, source: bytes):
        """Parse raw source bytes into a language-specific syntax tree."""
        raise NotImplementedError

    @abstractmethod
    def extract_imports(self, tree, source: bytes) -> list[RawImport]:
        """Extract import/dependency statements from a parsed tree."""
        raise NotImplementedError
