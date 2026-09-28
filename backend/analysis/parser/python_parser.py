from __future__ import annotations

import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser as TSParser

from analysis.parser.base import LanguageParser, RawImport

_PY_LANGUAGE = Language(tspython.language())


def _text(node: Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _dotted_name_text(node: Node, source: bytes) -> str:
    """`dotted_name` nodes contain identifier/'.' children; join them."""
    return _text(node, source)


class PythonParser(LanguageParser):
    """Extracts `import` / `from ... import ...` statements from Python
    source using Tree-sitter (grammar-accurate, not regex).

    Deliberately NOT extracted yet (see currentplan.docx §4D — later
    dependency types): function calls, class instantiation, inheritance,
    dynamic imports (importlib), star-imports resolution.
    """

    extensions = (".py",)

    def __init__(self) -> None:
        self._parser = TSParser(_PY_LANGUAGE)

    def parse(self, source: bytes):
        return self._parser.parse(source)

    def extract_imports(self, tree, source: bytes) -> list[RawImport]:
        imports: list[RawImport] = []
        self._walk(tree.root_node, source, imports)
        return imports

    def _walk(self, node: Node, source: bytes, out: list[RawImport]) -> None:
        if node.type == "import_statement":
            out.extend(self._handle_import_statement(node, source))
        elif node.type == "import_from_statement":
            imp = self._handle_import_from_statement(node, source)
            if imp is not None:
                out.append(imp)
        else:
            for child in node.children:
                self._walk(child, source, out)
            return
        # still recurse into children in case of nested statements (rare)
        for child in node.children:
            self._walk(child, source, out)

    def _handle_import_statement(self, node: Node, source: bytes) -> list[RawImport]:
        """`import a.b`, `import a.b as c`, `import a, b as c`"""
        results: list[RawImport] = []
        line = node.start_point[0] + 1
        for child in node.children:
            if child.type == "dotted_name":
                module = _dotted_name_text(child, source)
                results.append(RawImport(module=module, imported_names=(), line=line))
            elif child.type == "aliased_import":
                dotted = child.child_by_field_name("name") or next(
                    (c for c in child.children if c.type == "dotted_name"), None
                )
                if dotted is not None:
                    module = _dotted_name_text(dotted, source)
                    results.append(RawImport(module=module, imported_names=(), line=line))
        return results

    def _handle_import_from_statement(self, node: Node, source: bytes) -> RawImport | None:
        """`from a.b import c, d`, `from . import x`, `from .a import b`

        The `import` keyword token reliably separates the module clause
        (before it) from the imported-names clause (after it) — relying
        on this instead of "first dotted_name wins" avoids misreading
        `from . import database` as module='database'.
        """
        line = node.start_point[0] + 1
        module_text = ""
        is_relative = False
        imported_names: list[str] = []
        past_import_keyword = False

        for child in node.children:
            if child.type == "import" and not past_import_keyword:
                past_import_keyword = True
                continue

            if not past_import_keyword:
                if child.type == "dotted_name":
                    module_text = _dotted_name_text(child, source)
                elif child.type == "relative_import":
                    is_relative = True
                    # full text preserves leading dots, e.g. ".", ".models", "..shared"
                    module_text = _text(child, source)
            else:
                if child.type == "dotted_name":
                    imported_names.append(_dotted_name_text(child, source))
                elif child.type == "aliased_import":
                    dotted = next(
                        (c for c in child.children if c.type == "dotted_name"), None
                    )
                    if dotted is not None:
                        imported_names.append(_dotted_name_text(dotted, source))
                elif child.type == "wildcard_import":
                    imported_names.append("*")

        if not module_text and not is_relative:
            return None
        return RawImport(
            module=module_text,
            imported_names=tuple(imported_names),
            line=line,
            is_relative=is_relative,
        )
