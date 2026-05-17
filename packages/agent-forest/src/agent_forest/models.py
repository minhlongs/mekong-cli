"""Pydantic request/response schemas shared by gateway routes."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=256)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfile(BaseModel):
    user_id: str
    username: str


class TaskRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    webhook_url: str | None = None


class TaskEnqueued(BaseModel):
    job_id: str
    status: str
    created_at: str


class JobRecord(BaseModel):
    job_id: str
    user_id: str
    prompt: str
    status: str
    created_at: str
    updated_at: str
    webhook_url: str | None = None
    result: str | None = None
    error: str | None = None


class FeedbackRequest(BaseModel):
    """User-rating payload for POST /task/{job_id}/feedback (Giai đoạn 3.2.B)."""

    rating: str = Field(pattern="^(good|bad)$")
    note: str | None = Field(default=None, max_length=500)


class FeedbackAccepted(BaseModel):
    job_id: str
    rating: str
    forwarded: bool
