from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response, status

from app.modules.auth.dependencies import CurrentSession, DatabaseSession
from app.modules.tasks import service
from app.modules.tasks.schemas import TaskCreate, TaskPage, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])
TaskId = Annotated[int, Path(gt=0, le=2**63 - 1)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate, session: CurrentSession, db: DatabaseSession) -> TaskRead:
    try:
        return service.create_task(db, session.user_id, data)
    except service.TaskOwnerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task owner not found") from exc


@router.get("")
def list_tasks(
    session: CurrentSession,
    db: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    after_id: Annotated[int | None, Query(ge=1, le=2**63 - 1)] = None,
) -> TaskPage:
    return service.list_tasks(db, session.user_id, limit=limit, after_id=after_id)


@router.get("/{task_id}")
def get_task(task_id: TaskId, session: CurrentSession, db: DatabaseSession) -> TaskRead:
    try:
        return service.get_task(db, task_id, session.user_id)
    except service.TaskNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found") from exc


@router.patch("/{task_id}")
def update_task(
    task_id: TaskId, data: TaskUpdate, session: CurrentSession, db: DatabaseSession
) -> TaskRead:
    try:
        return service.update_task(db, task_id, session.user_id, data)
    except service.TaskNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found") from exc


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: TaskId, session: CurrentSession, db: DatabaseSession) -> Response:
    try:
        service.delete_task(db, task_id, session.user_id)
    except service.TaskNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
