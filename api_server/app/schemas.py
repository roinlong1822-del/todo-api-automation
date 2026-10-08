"""请求/响应模型(契约即代码)。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=64)


class TokenResponse(BaseModel):
    token: str
    expires_in: int


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    priority: int = Field(default=1, ge=1, le=3)


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    priority: int
    status: Literal["pending", "done"]


class TodoListOut(BaseModel):
    total: int
    page: int
    size: int
    items: list[TodoOut]


class ErrorOut(BaseModel):
    code: str
    message: str
