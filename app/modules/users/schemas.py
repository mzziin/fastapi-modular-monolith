from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    field_validator,
)
from pydantic.json_schema import SkipJsonSchema

UserName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class UserCreate(BaseModel):
    name: UserName
    email: EmailStr
    password: SecretStr = Field(min_length=8)


class UserUpdate(BaseModel):
    name: UserName | SkipJsonSchema[None] = None
    email: EmailStr | SkipJsonSchema[None] = None

    @field_validator("name", "email")
    @classmethod
    def reject_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime
