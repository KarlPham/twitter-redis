from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID


# ─── Auth ─────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Users ────────────────────────────────────────────────────
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime


# ─── Posts ────────────────────────────────────────────────────
class CreatePostRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=280)


class PostResponse(BaseModel):
    id: UUID
    user_id: UUID
    body: str
    created_at: datetime
    username: str | None = None


# ─── Follows ──────────────────────────────────────────────────
class FollowResponse(BaseModel):
    message: str
    following: str