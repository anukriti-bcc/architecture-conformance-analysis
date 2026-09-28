from backend.repositories.user_repository import UserRepository


class UserService:
    """Service layer — business logic. Talks to the database only through
    a Repository, never directly."""

    def __init__(self):
        self.repository = UserRepository()

    def get_user(self, user_id: int):
        return self.repository.find_by_id(user_id)

    def register_user(self, user_data: dict):
        return self.repository.save(user_data)
