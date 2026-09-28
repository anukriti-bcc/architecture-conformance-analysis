"""Database connection utilities — the bottom layer of the architecture.

Nothing in this file should ever import from services/, controllers/, or
repositories/; the dependency arrow only ever points INTO this module.
"""


class DatabaseConnection:
    def __init__(self, dsn: str = "postgresql://localhost/sample_ecommerce"):
        self.dsn = dsn
        self._connected = False

    def connect(self):
        self._connected = True
        return self

    def execute(self, query: str, params: tuple = ()):
        if not self._connected:
            raise RuntimeError("Not connected")
        # Placeholder — Milestone 1 only needs realistic import structure,
        # not a working database.
        return []


def get_connection() -> DatabaseConnection:
    return DatabaseConnection().connect()
