from sqlalchemy.orm import Session

from app.modules.tasks import repository
from app.modules.tasks.models import Task
from app.modules.tasks.repository import (
    TaskOwnerNotFoundError as TaskOwnerNotFoundError,
)
from app.modules.tasks.schemas import TaskCreate, TaskPage, TaskRead, TaskUpdate


class TaskNotFoundError(Exception):
    pass


def list_tasks(
    db: Session, owner_id: int, *, limit: int, after_id: int | None
) -> TaskPage:
    tasks = repository.list_tasks(db, owner_id, limit=limit + 1, after_id=after_id)
    return TaskPage(
        items=[TaskRead.model_validate(task) for task in tasks[:limit]],
        next_after_id=tasks[limit - 1].id if len(tasks) > limit else None,
    )


def _read_task(task: Task | None) -> TaskRead:
    if task is None:
        raise TaskNotFoundError
    return TaskRead.model_validate(task)


def get_task(db: Session, task_id: int, owner_id: int) -> TaskRead:
    return _read_task(repository.get_task(db, task_id, owner_id))


def create_task(db: Session, owner_id: int, data: TaskCreate) -> TaskRead:
    task = Task(owner_id=owner_id, **data.model_dump())
    return TaskRead.model_validate(repository.create_task(db, task))


def update_task(db: Session, task_id: int, owner_id: int, data: TaskUpdate) -> TaskRead:
    changes = data.model_dump(exclude_unset=True)
    return _read_task(repository.update_task(db, task_id, owner_id, changes))


def delete_task(db: Session, task_id: int, owner_id: int) -> None:
    if not repository.delete_task(db, task_id, owner_id):
        raise TaskNotFoundError
