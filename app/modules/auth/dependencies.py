from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth import service

bearer = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: DatabaseSession,
) -> service.AuthenticatedSession:
    if credentials is not None:
        session = service.authenticate(db, credentials.credentials)
        if session is not None:
            return session
    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Missing or invalid session",
        headers={"WWW-Authenticate": "Bearer"},
    )


CurrentSession = Annotated[service.AuthenticatedSession, Depends(get_current_session)]
