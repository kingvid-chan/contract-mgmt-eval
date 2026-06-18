"""User request/response schemas."""

from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="user", pattern="^(admin|user)$")


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=2, max_length=50)
    email: str | None = Field(None, max_length=100)
    password: str | None = Field(None, min_length=6, max_length=100)
    role: str | None = Field(None, pattern="^(admin|user)$")


class UserStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|disabled)$")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total: int
    items: list[UserResponse]
