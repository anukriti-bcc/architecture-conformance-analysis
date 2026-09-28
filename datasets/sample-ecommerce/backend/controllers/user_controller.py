from backend.services.user_service import UserService


class UserController:
    """Controller layer — talks to Services only, never Repositories or
    the database directly."""

    def __init__(self):
        self.service = UserService()

    def get(self, user_id: int):
        return self.service.get_user(user_id)

    def register(self, user_data: dict):
        return self.service.register_user(user_data)
