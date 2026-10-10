"""
Pytest fixtures using `moto` to mock Amazon S3 + DynamoDB in-memory.

This exercises the REAL boto3 code paths (put_object, query, get_item, ...)
against a faithful AWS mock, so the tests prove the AWS integration works —
no real AWS account or credentials required.
"""
import os
import sys
from pathlib import Path

import boto3
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Deterministic, fake AWS env BEFORE anything imports the app config.
os.environ.update({
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_REGION": "us-east-1",
    "S3_BUCKET_NAME": "test-backup-bucket",
    "DYNAMODB_TABLE_NAME": "BackupFiles",
    "DYNAMODB_USERS_TABLE": "BackupUsers",
    "JWT_SECRET": "test-secret-key-for-pytest-only",
})

from moto import mock_aws  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def aws(monkeypatch):
    """Spin up mocked S3 + DynamoDB with the bucket and tables created."""
    with mock_aws():
        region = "us-east-1"

        # S3 bucket holds BOTH the files and the JSON metadata objects.
        s3 = boto3.client("s3", region_name=region)
        s3.create_bucket(Bucket="test-backup-bucket")

        # Make sure the app builds fresh boto3 clients INSIDE the mock context.
        from server.services import aws_clients
        aws_clients.reset_clients()

        yield
        aws_clients.reset_clients()


@pytest.fixture
def client(aws):
    from server.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register a user and return ready-to-use Authorization headers."""
    resp = client.post("/auth/register", json={
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
