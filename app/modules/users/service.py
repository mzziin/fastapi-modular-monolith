from secrets import token_urlsafe

from pydantic import SecretStr
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.modules.users import repository
from app.modules.users.models import User
from app.modules.users.repository import (
    EmailAlreadyExistsError as EmailAlreadyExistsError,
    UserNotFoundError as UserNotFoundError,
)
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate

password_hasher = PasswordHash.recommended()
dummy_password_hash = password_hasher.hash(token_urlsafe(32))


def verify_credentials(db: Session, email: str, password: SecretStr) -> int | None:
    user = repository.get_user_by_email(db, email)
    stored_hash = user.password_hash if user is not None else dummy_password_hash
    matches = password_hasher.verify(password.get_secret_value(), stored_hash)
    if matches and user is not None:
        return user.id
    return None


def _require_user(db: Session, user_id: int) -> User:
    user = repository.get_user(db, user_id)
    if user is None:
        raise UserNotFoundError
    return user


def get_user(db: Session, user_id: int) -> UserRead:
    return UserRead.model_validate(_require_user(db, user_id))


def create_user(db: Session, data: UserCreate) -> UserRead:
    user = User(
        name=data.name,
        email=data.email,
        password_hash=password_hasher.hash(data.password.get_secret_value()),
    )
    return UserRead.model_validate(repository.create_user(db, user))


def update_user(db: Session, user_id: int, data: UserUpdate) -> UserRead:
    user = _require_user(db, user_id)
    changes = data.model_dump(exclude_unset=True)
    return UserRead.model_validate(repository.update_user(db, user, changes))


def delete_user(db: Session, user_id: int) -> None:
    user = _require_user(db, user_id)
    repository.delete_user(db, user)
