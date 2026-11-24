from psycopg.errors import ForeignKeyViolation
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import AuthSession


def create_session(db: Session, session: AuthSession, now: int) -> bool:
    try:
        db.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
        db.add(session)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if isinstance(exc.orig, ForeignKeyViolation):
            return False
        raise
    return True


def get_active_session(db: Session, token_digest: str, now: int) -> AuthSession | None:
    return db.scalar(
        select(AuthSession).where(
            AuthSession.token_digest == token_digest, AuthSession.expires_at > now
        )
    )


def revoke_session(db: Session, token_digest: str) -> None:
    db.execute(delete(AuthSession).where(AuthSession.token_digest == token_digest))
    db.commit()
