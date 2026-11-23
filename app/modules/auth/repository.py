from psycopg.errors import ForeignKeyViolation
from sqlalchemy import case, delete, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.auth.models import AuthSession, LoginAttemptWindow


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


def _record_attempt(
    db: Session, key: str, limit: int, now: int, window_seconds: int
) -> int:
    expired = LoginAttemptWindow.expires_at <= now
    statement = insert(LoginAttemptWindow).values(
        key=key, attempts=1, expires_at=now + window_seconds
    )
    statement = statement.on_conflict_do_update(
        index_elements=[LoginAttemptWindow.key],
        set_={
            "attempts": case((expired, 1), else_=LoginAttemptWindow.attempts + 1),
            "expires_at": case((expired, now + window_seconds), else_=LoginAttemptWindow.expires_at),
        },
        where=or_(expired, LoginAttemptWindow.attempts < limit),
    ).returning(LoginAttemptWindow.attempts)
    if db.scalar(statement) is not None:
        return 0
    expires_at = db.execute(
        select(LoginAttemptWindow.expires_at).where(LoginAttemptWindow.key == key)
    ).scalar_one()
    return expires_at - now


def record_login_attempt(
    db: Session, buckets: tuple[tuple[str, int], ...], now: int, window_seconds: int
) -> int:
    retry_after = 0
    with db.begin():
        for key, limit in buckets:
            retry_after = _record_attempt(db, key, limit, now, window_seconds)
            if retry_after:
                break

        # Cleanup must not wait on counters another login is updating.
        expired_keys = (
            select(LoginAttemptWindow.key)
            .where(LoginAttemptWindow.expires_at <= now)
            .with_for_update(skip_locked=True)
        )
        db.execute(delete(LoginAttemptWindow).where(LoginAttemptWindow.key.in_(expired_keys)))
    return retry_after
