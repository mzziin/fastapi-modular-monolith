from dataclasses import dataclass
from hashlib import sha256
from secrets import token_urlsafe
from time import time

from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.auth import repository
from app.modules.auth.models import AuthSession
from app.modules.auth.schemas import LoginRequest, SessionToken
from app.modules.users import service as users_service


class InvalidCredentialsError(Exception):
    pass


class LoginRateLimitError(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after


@dataclass(frozen=True)
class AuthenticatedSession:
    user_id: int
    token_digest: str


def _digest(value: str) -> str:
    return sha256(value.encode()).hexdigest()


def login(db: Session, data: LoginRequest, client_host: str) -> SessionToken:
    buckets = (
        (_digest(f"ip:{client_host}"), 20),
        (_digest(f"email:{data.email.casefold()}"), 10),
    )
    retry_after = repository.record_login_attempt(db, buckets, int(time()), 60)
    if retry_after:
        raise LoginRateLimitError(retry_after)

    user_id = users_service.verify_credentials(db, data.email, data.password)
    if user_id is None:
        raise InvalidCredentialsError

    token = token_urlsafe(32)
    now = int(time())
    expires_in = settings.auth_session_ttl_seconds
    session = AuthSession(
        user_id=user_id, token_digest=_digest(token), expires_at=now + expires_in
    )
    if not repository.create_session(db, session, now):
        raise InvalidCredentialsError
    return SessionToken(access_token=token, expires_in=expires_in)


def authenticate(db: Session, token: str) -> AuthenticatedSession | None:
    session = repository.get_active_session(db, _digest(token), int(time()))
    if session is None:
        return None
    return AuthenticatedSession(user_id=session.user_id, token_digest=session.token_digest)


def logout(db: Session, session: AuthenticatedSession) -> None:
    repository.revoke_session(db, session.token_digest)
