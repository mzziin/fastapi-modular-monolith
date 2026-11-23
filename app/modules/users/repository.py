from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.modules.users.models import User


class EmailAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def _commit_user(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if isinstance(exc.orig, UniqueViolation):
            raise EmailAlreadyExistsError from exc
        raise
    except StaleDataError as exc:
        db.rollback()
        raise UserNotFoundError from exc


def create_user(db: Session, user: User) -> User:
    db.add(user)
    _commit_user(db)
    return user


def update_user(db: Session, user: User, changes: dict[str, str]) -> User:
    for field, value in changes.items():
        setattr(user, field, value)
    _commit_user(db)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
