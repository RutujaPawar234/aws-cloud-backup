"""
DynamoDB metadata layer.

Two tables:
  * Users table  (PK: email)         -> account records (bcrypt hash)
  * BackupFiles  (PK: user_id,
                  SK: file_id)        -> one row per backed-up file

Storing files with user_id as the partition key lets us fetch all of a user's
files with a single efficient Query, and guarantees users only see their own.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from boto3.dynamodb.conditions import Key

from server.config import get_settings
from server.services.aws_clients import get_dynamodb_resource


# ----------------------------------------------------------------- helpers
def _users_table():
    return get_dynamodb_resource().Table(get_settings().DYNAMODB_USERS_TABLE)


def _files_table():
    return get_dynamodb_resource().Table(get_settings().DYNAMODB_TABLE_NAME)


def _clean(item: Optional[dict]) -> Optional[dict]:
    """Convert DynamoDB Decimals back to plain ints for JSON responses."""
    if item is None:
        return None
    out = dict(item)
    for k, v in out.items():
        if isinstance(v, Decimal):
            out[k] = int(v)
    return out


# ------------------------------------------------------------------- users
def get_user_by_email(email: str) -> Optional[dict]:
    """Return the user record for an email, or None."""
    res = _users_table().get_item(Key={"email": email.lower()})
    return res.get("Item")


def create_user_record(full_name: str, email: str, password_hash: str) -> dict:
    """Insert a new user. Raises ValueError('email_exists') on duplicate."""
    email = email.lower()
    if get_user_by_email(email):
        raise ValueError("email_exists")

    user_id = str(uuid.uuid4())
    item = {
        "email": email,
        "id": user_id,
        "full_name": full_name.strip(),
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _users_table().put_item(Item=item)
    public = dict(item)
    public.pop("password_hash", None)
    return public


# ------------------------------------------------------------------- files
def save_file_metadata(
    user_id: str, file_name: str, file_size: int, file_type: str, s3_key: str
) -> dict:
    """Store one file's metadata and return it."""
    item = {
        "user_id": user_id,
        "file_id": str(uuid.uuid4()),
        "file_name": file_name,
        "file_size": file_size,
        "file_type": file_type,
        "s3_key": s3_key,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "status": "Backed Up",
    }
    _files_table().put_item(Item=item)
    return _clean(item)


def list_user_files(user_id: str) -> list[dict]:
    """Return all of a user's file metadata rows (newest first)."""
    res = _files_table().query(
        KeyConditionExpression=Key("user_id").eq(user_id)
    )
    items = [_clean(i) for i in res.get("Items", [])]
    items.sort(key=lambda r: r.get("uploaded_at", ""), reverse=True)
    return items


def get_file_metadata(user_id: str, file_id: str) -> Optional[dict]:
    """Return one metadata row IF it belongs to the user, else None."""
    res = _files_table().get_item(Key={"user_id": user_id, "file_id": file_id})
    return _clean(res.get("Item"))


def delete_file_metadata(user_id: str, file_id: str) -> None:
    """Delete one metadata row."""
    _files_table().delete_item(Key={"user_id": user_id, "file_id": file_id})
