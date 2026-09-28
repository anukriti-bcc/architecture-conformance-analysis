from backend.database.connection import get_connection


class PaymentRepository:
    """Repository layer for payments — the sanctioned path to the database."""

    def __init__(self):
        self.db = get_connection()

    def save_transaction(self, transaction: dict):
        return self.db.execute("INSERT INTO transactions (...) VALUES (...)", (transaction,))

    def find_by_order_id(self, order_id: int):
        return self.db.execute(
            "SELECT * FROM transactions WHERE order_id = %s", (order_id,)
        )
