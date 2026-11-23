from collections.abc import Sequence

from psycopg.errors import ForeignKeyViolation
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.tasks.models import Task


class TaskOwnerNotFoundError(Exception):
    pass


def list_tasks(
    db: Session, owner_id: int, *, limit: int, after_id: int | None
) -> Sequence[Task]:
    statement = select(Task).where(Task.owner_id == owner_id)
    if after_id is not None:
        statement = statement.where(Task.id > after_id)
    return db.scalars(statement.order_by(Task.id).limit(limit)).all()


def get_task(db: Session, task_id: int, owner_id: int) -> Task | None:
    return db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == owner_id))


def create_task(db: Session, task: Task) -> Task:
    db.add(task)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if isinstance(exc.orig, ForeignKeyViolation):
            raise TaskOwnerNotFoundError from exc
        raise
    return task


def update_task(
    db: Session, task_id: int, owner_id: int, changes: dict[str, str | bool | None]
) -> Task | None:
    if not changes:
        return get_task(db, task_id, owner_id)
    task = db.scalar(
        update(Task)
        .where(Task.id == task_id, Task.owner_id == owner_id)
        .values(**changes)
        .returning(Task)
    )
    db.commit()
    return task


def delete_task(db: Session, task_id: int, owner_id: int) -> bool:
    deleted_id = db.scalar(
        delete(Task).where(Task.id == task_id, Task.owner_id == owner_id).returning(Task.id)
    )
    db.commit()
    return deleted_id is not None
