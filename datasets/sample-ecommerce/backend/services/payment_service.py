from backend.repositories.payment_repository import PaymentRepository


class PaymentService:
    """Service layer for payments.

    Most of this class correctly goes through PaymentRepository. One
    method, `refund`, was written in a hurry during a "temporary" hotfix
    and reaches directly into the database layer instead — the kind of
    small, easy-to-miss shortcut that architectural drift usually looks
    like in real codebases. This is the deliberate violation the demo
    is built to catch.
    """

    def __init__(self):
        self.repository = PaymentRepository()

    def charge(self, order_id: int, amount: float):
        transaction = {"order_id": order_id, "amount": amount, "status": "charged"}
        return self.repository.save_transaction(transaction)

    def get_transaction(self, order_id: int):
        return self.repository.find_by_order_id(order_id)

    def _validate_amount(self, amount: float) -> bool:
        return amount > 0

    def _build_receipt(self, transaction: dict) -> dict:
        return {
            "order_id": transaction.get("order_id"),
            "amount": transaction.get("amount"),
            "status": transaction.get("status"),
        }

    def _log_payment_event(self, event: str, order_id: int):
        # placeholder for future audit logging
        pass

    def refund(self, order_id: int, amount: float):
        """Refund a payment.

        NOTE: this bypasses PaymentRepository and hits the database
        connection directly — this is the architectural violation.
        """
        from backend.database.connection import get_connection  # VIOLATION: service -> database

        db = get_connection()
        return db.execute(
            "UPDATE transactions SET status = 'refunded' WHERE order_id = %s",
            (order_id,),
        )
