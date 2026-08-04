import psycopg
from psycopg.rows import dict_row

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    _table = "users"
    _model = User

    def get_by_email(self, db: psycopg.Connection, email: str) -> User | None:
        with db.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,),
            )
            return self._row_to_obj(cur.fetchone())


user_repository = UserRepository()
