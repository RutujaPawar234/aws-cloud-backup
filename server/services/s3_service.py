"""
Amazon S3 file layer.

Objects are stored as:  backups/<user_id>/<uuid>__<original file name>
The uuid keeps the key unique so re-uploading the same name is always safe,
while the original name is preserved for restore.
"""
from __future__ import annotations

import uuid

from server.config import get_settings
from server.services.aws_clients import get_s3


def build_s3_key(user_id: str, file_name: str) -> str:
    """Create a unique, per-user S3 object key that preserves the file name."""
    unique = uuid.uuid4().hex[:12]
    return f"backups/{user_id}/{unique}__{file_name}"


def upload_file_to_s3(s3_key: str, data: bytes, content_type: str) -> None:
    """Upload raw bytes to S3 under the given key."""
    get_s3().put_object(
        Bucket=get_settings().S3_BUCKET_NAME,
        Key=s3_key,
        Body=data,
        ContentType=content_type or "application/octet-stream",
    )


def download_file_from_s3(s3_key: str) -> bytes:
    """Download an object's bytes from S3."""
    obj = get_s3().get_object(Bucket=get_settings().S3_BUCKET_NAME, Key=s3_key)
    return obj["Body"].read()


def delete_file_from_s3(s3_key: str) -> None:
    """Delete an object from S3 (no error if it is already gone)."""
    get_s3().delete_object(Bucket=get_settings().S3_BUCKET_NAME, Key=s3_key)
