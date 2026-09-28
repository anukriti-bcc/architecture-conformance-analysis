from backend.database.connection import get_connection


class UserRepository:
    """Repository layer — the ONLY layer allowed to talk to the database."""

    def __init__(self):
        self.db = get_connection()

    def find_by_id(self, user_id: int):
        return self.db.execute("SELECT * FROM users WHERE id = %s", (user_id,))

    def save(self, user: dict):
        return self.db.execute("INSERT INTO users (...) VALUES (...)", (user,))
