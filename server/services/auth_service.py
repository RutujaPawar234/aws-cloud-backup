"""
User registration and login backed by the DynamoDB users table.

Passwords are stored ONLY as bcrypt hashes (attribute: password_hash).
"""
from __future__ import annotations

from typing import Optional

# Metadata backend: S3-backed (works everywhere). Swap this single import to
# `dynamodb_service` if your AWS account allows DynamoDB and you prefer it.
from server.services import metadata_service as metadata_backend
from server.utils.security import hash_password, verify_password


def create_user(full_name: str, email: str, password: str) -> dict:
    """
    Create a new user. Returns the public record (no hash).
    Raises ValueError('email_exists') if the email is taken.
    """
    return metadata_backend.create_user_record(
        full_name=full_name,
        email=email,
        password_hash=hash_password(password),
    )


def authenticate(email: str, password: str) -> Optional[dict]:
    """Verify credentials. Returns the public user record, or None."""
    user = metadata_backend.get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.get("password_hash", "")):
        return None
    public = dict(user)
    public.pop("password_hash", None)
    return public
