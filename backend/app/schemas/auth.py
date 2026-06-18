"""Authentication request/response schemas."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=100)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfoResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str

    model_config = {"from_attributes": True}


class PasswordResetRequest(BaseModel):
    email: str = Field(..., max_length=100)


class PasswordResetResponse(BaseModel):
    message: str
    new_password: str | None = None


class MessageResponse(BaseModel):
    message: str
