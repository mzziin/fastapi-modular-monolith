from fastapi import APIRouter, HTTPException, Response, status

from app.modules.auth.dependencies import CurrentSession, DatabaseSession
from app.modules.users import service
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: DatabaseSession) -> UserRead:
    try:
        return service.create_user(db, data)
    except service.EmailAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists") from exc


@router.get("/me")
def get_current_user(session: CurrentSession, db: DatabaseSession) -> UserRead:
    try:
        return service.get_user(db, session.user_id)
    except service.UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from exc


@router.patch("/me")
def update_current_user(
    data: UserUpdate, session: CurrentSession, db: DatabaseSession
) -> UserRead:
    try:
        return service.update_user(db, session.user_id, data)
    except service.UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from exc
    except service.EmailAlreadyExistsError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists") from exc


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(session: CurrentSession, db: DatabaseSession) -> Response:
    try:
        service.delete_user(db, session.user_id)
    except service.UserNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
