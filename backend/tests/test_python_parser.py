from analysis.parser.python_parser import PythonParser


def _imports(code: str):
    parser = PythonParser()
    source = code.encode("utf-8")
    tree = parser.parse(source)
    return parser.extract_imports(tree, source)


def test_simple_absolute_import():
    imports = _imports("import os\n")
    assert len(imports) == 1
    assert imports[0].module == "os"
    assert imports[0].is_relative is False


def test_dotted_absolute_import():
    imports = _imports("import database.connection\n")
    assert imports[0].module == "database.connection"


def test_aliased_import():
    imports = _imports("import database.connection as dbconn\n")
    assert imports[0].module == "database.connection"


def test_from_import_multiple_names():
    imports = _imports("from services.payment import PaymentService, Foo\n")
    assert len(imports) == 1
    assert imports[0].module == "services.payment"
    assert imports[0].imported_names == ("PaymentService", "Foo")
    assert imports[0].is_relative is False


def test_relative_import_bare_dot():
    imports = _imports("from . import database\n")
    assert imports[0].module == "."
    assert imports[0].imported_names == ("database",)
    assert imports[0].is_relative is True


def test_relative_import_single_level():
    imports = _imports("from .models import User\n")
    assert imports[0].module == ".models"
    assert imports[0].imported_names == ("User",)
    assert imports[0].is_relative is True


def test_relative_import_multi_level():
    imports = _imports("from ..shared import util\n")
    assert imports[0].module == "..shared"
    assert imports[0].is_relative is True


def test_wildcard_import():
    imports = _imports("from services.payment import *\n")
    assert imports[0].imported_names == ("*",)


def test_import_line_number():
    code = "import os\nimport sys\n\nfrom services.payment import PaymentService\n"
    imports = _imports(code)
    assert imports[0].line == 1
    assert imports[1].line == 2
    assert imports[2].line == 4


def test_ignores_non_import_code():
    code = "x = 1\ndef foo():\n    return x\n"
    assert _imports(code) == []
