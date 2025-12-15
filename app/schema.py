from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str
    username: Annotated[str, Field(min_length=1)]
    password: Annotated[str, Field(min_length=8)]


class UserRead(BaseModel):
    id: UUID
    name: str
    username: str

    model_config = {"from_attributes": True}
