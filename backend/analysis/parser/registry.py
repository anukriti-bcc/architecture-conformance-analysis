from __future__ import annotations

from analysis.parser.base import LanguageParser
from analysis.parser.python_parser import PythonParser

# Milestone 1 supports Python only. Adding JavaScript/TypeScript later is
# a matter of writing analysis/parser/javascript_parser.py implementing
# LanguageParser and registering it here — nothing else in the pipeline
# needs to change (see currentplan.docx §1 "Language support").
_PARSERS: list[LanguageParser] = [
    PythonParser(),
]

_EXTENSION_MAP: dict[str, LanguageParser] = {
    ext: parser for parser in _PARSERS for ext in parser.extensions
}


def get_parser_for_file(path: str) -> LanguageParser | None:
    for ext, parser in _EXTENSION_MAP.items():
        if path.endswith(ext):
            return parser
    return None


def supported_extensions() -> tuple[str, ...]:
    return tuple(_EXTENSION_MAP.keys())
