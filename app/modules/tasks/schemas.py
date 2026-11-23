from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator
from pydantic.json_schema import SkipJsonSchema

TaskTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TaskTitle
    description: str | None = None
    is_completed: bool = False


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TaskTitle | SkipJsonSchema[None] = None
    description: str | None = None
    is_completed: bool | SkipJsonSchema[None] = None

    @field_validator("title", "is_completed")
    @classmethod
    def reject_null(cls, value: str | bool | None) -> str | bool:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    owner_id: int
    description: str | None
    is_completed: bool
    created_at: datetime


class TaskPage(BaseModel):
    items: list[TaskRead]
    next_after_id: int | None
