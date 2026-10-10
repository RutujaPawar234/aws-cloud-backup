"""
Metadata store backed by Amazon S3 (JSON objects).

Used instead of DynamoDB when the AWS account cannot use DynamoDB (e.g. an
Organizations SCP blocks it). It exposes the SAME function names as
dynamodb_service, so the rest of the app does not care which backend is used.

Layout inside the same bucket that stores the files:
  users/<email>.json                      -> account record (bcrypt hash)
  metadata/<user_id>/<file_id>.json       -> one file's metadata
  backups/<user_id>/<uuid>__<name>        -> the actual file bytes (s3_service)
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from botocore.exceptions import ClientError

from server.config import get_settings
from server.services.aws_clients import get_s3

_USERS_PREFIX = "users/"
_META_PREFIX = "metadata/"


def _bucket() -> str:
    return get_settings().S3_BUCKET_NAME


def _put_json(key: str, obj: dict) -> None:
    get_s3().put_object(
        Bucket=_bucket(),
        Key=key,
        Body=json.dumps(obj).encode("utf-8"),
        ContentType="application/json",
    )


def _get_json(key: str) -> Optional[dict]:
    try:
        res = get_s3().get_object(Bucket=_bucket(), Key=key)
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("NoSuchKey", "404", "NoSuchBucket"):
            return None
        raise
    return json.loads(res["Body"].read().decode("utf-8"))


# ------------------------------------------------------------------- users
def _user_key(email: str) -> str:
    return f"{_USERS_PREFIX}{email.lower()}.json"


def get_user_by_email(email: str) -> Optional[dict]:
    """Return the user record for an email, or None."""
    return _get_json(_user_key(email))


def create_user_record(full_name: str, email: str, password_hash: str) -> dict:
    """Insert a new user. Raises ValueError('email_exists') on duplicate."""
    email = email.lower()
    if get_user_by_email(email):
        raise ValueError("email_exists")

    item = {
        "id": str(uuid.uuid4()),
        "full_name": full_name.strip(),
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _put_json(_user_key(email), item)
    public = dict(item)
    public.pop("password_hash", None)
    return public


# ------------------------------------------------------------------- files
def _meta_key(user_id: str, file_id: str) -> str:
    return f"{_META_PREFIX}{user_id}/{file_id}.json"


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
    _put_json(_meta_key(user_id, item["file_id"]), item)
    return item


def list_user_files(user_id: str) -> list[dict]:
    """Return all of a user's file metadata rows (newest first)."""
    s3 = get_s3()
    prefix = f"{_META_PREFIX}{user_id}/"
    items: list[dict] = []

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=_bucket(), Prefix=prefix):
        for obj in page.get("Contents", []):
            data = _get_json(obj["Key"])
            if data:
                items.append(data)

    items.sort(key=lambda r: r.get("uploaded_at", ""), reverse=True)
    return items


def get_file_metadata(user_id: str, file_id: str) -> Optional[dict]:
    """Return one metadata row IF it belongs to the user, else None."""
    return _get_json(_meta_key(user_id, file_id))


def delete_file_metadata(user_id: str, file_id: str) -> None:
    """Delete one metadata row."""
    get_s3().delete_object(Bucket=_bucket(), Key=_meta_key(user_id, file_id))
