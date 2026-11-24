from fastapi import APIRouter, HTTPException, Request, Response, status

from app.modules.auth import service
from app.modules.auth.dependencies import CurrentSession, DatabaseSession
from app.modules.auth.schemas import LoginRequest, SessionToken

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    data: LoginRequest, request: Request, response: Response, db: DatabaseSession
) -> SessionToken:
    client_host = request.client.host if request.client else "unknown"
    try:
        token = service.login(db, data, client_host, request.app.state.redis)
    except service.InvalidCredentialsError as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except service.LoginRateLimitError as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many login attempts",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc
    except service.RateLimiterUnavailableError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Login temporarily unavailable"
        ) from exc
    response.headers["Cache-Control"] = "no-store"
    return token


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(session: CurrentSession, db: DatabaseSession) -> Response:
    service.logout(db, session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
