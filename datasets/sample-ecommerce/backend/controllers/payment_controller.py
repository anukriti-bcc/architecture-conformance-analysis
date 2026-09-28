from backend.services.payment_service import PaymentService


class PaymentController:
    """Controller layer for payments — talks to PaymentService only."""

    def __init__(self):
        self.service = PaymentService()

    def charge(self, order_id: int, amount: float):
        return self.service.charge(order_id, amount)

    def refund(self, order_id: int, amount: float):
        return self.service.refund(order_id, amount)

    def get_transaction(self, order_id: int):
        return self.service.get_transaction(order_id)
