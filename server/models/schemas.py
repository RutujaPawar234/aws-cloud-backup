"""Pydantic request/response models used across the API."""
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# ---------- Files ----------
class FileMetadata(BaseModel):
    file_id: str
    user_id: str
    file_name: str
    file_size: int
    file_type: str
    s3_key: str
    uploaded_at: str
    status: str


class UploadResponse(BaseModel):
    message: str
    file: FileMetadata


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    aws_configured: bool
    region: str
    time: str
