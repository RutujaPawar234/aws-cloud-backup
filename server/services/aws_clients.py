"""
Boto3 client/resource factories.

The backend is the ONLY component that talks to AWS. Credentials come from the
environment (IAM user access keys), never from the desktop app. Because the
IAM user is scoped to just S3 + DynamoDB, the backend can only touch those.
"""
from __future__ import annotations

from typing import Optional

import boto3

from server.config import get_settings

_s3 = None
_dynamodb = None


def _session() -> boto3.session.Session:
    s = get_settings()
    return boto3.session.Session(
        aws_access_key_id=s.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=s.AWS_SECRET_ACCESS_KEY or None,
        region_name=s.AWS_REGION,
    )


def get_s3():
    """Return a shared S3 client. Raises RuntimeError if AWS isn't configured."""
    global _s3
    if not get_settings().aws_configured:
        raise RuntimeError("AWS is not configured. Set AWS_* and S3_BUCKET_NAME.")
    if _s3 is None:
        _s3 = _session().client("s3")
    return _s3


def get_dynamodb_resource():
    """Return a shared DynamoDB resource. Raises RuntimeError if not configured."""
    global _dynamodb
    if not get_settings().aws_configured:
        raise RuntimeError("AWS is not configured. Set AWS_* and S3_BUCKET_NAME.")
    if _dynamodb is None:
        _dynamodb = _session().resource("dynamodb")
    return _dynamodb


def reset_clients() -> None:
    """Drop cached clients (used by tests so mocks take effect)."""
    global _s3, _dynamodb
    _s3 = None
    _dynamodb = None
