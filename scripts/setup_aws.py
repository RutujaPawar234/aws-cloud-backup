"""
OPTIONAL helper: create the S3 bucket and DynamoDB tables this app needs.

It is safe and idempotent: it only CREATES resources if they are missing and
NEVER deletes anything. You can also create them by hand in the AWS Console
(see the README) — this script just saves time for the demo.

Run (after filling .env):
    python -m scripts.setup_aws
"""
from __future__ import annotations

import sys

from botocore.exceptions import ClientError

# Make `server` importable when run as a script.
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.config import get_settings  # noqa: E402
from server.services.aws_clients import get_dynamodb_resource, get_s3  # noqa: E402


def ensure_bucket() -> None:
    s = get_settings()
    s3 = get_s3()
    try:
        s3.head_bucket(Bucket=s.S3_BUCKET_NAME)
        print(f"[ok]   S3 bucket already exists: {s.S3_BUCKET_NAME}")
        return
    except ClientError:
        pass

    # us-east-1 must NOT send a LocationConstraint; every other region must.
    kwargs = {"Bucket": s.S3_BUCKET_NAME}
    if s.AWS_REGION != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": s.AWS_REGION}
    s3.create_bucket(**kwargs)
    print(f"[new]  Created S3 bucket: {s.S3_BUCKET_NAME}")


def ensure_table(name: str, key_schema: list, attr_defs: list) -> None:
    ddb = get_dynamodb_resource()
    existing = [t.name for t in ddb.tables.all()]
    if name in existing:
        print(f"[ok]   DynamoDB table already exists: {name}")
        return
    table = ddb.create_table(
        TableName=name,
        KeySchema=key_schema,
        AttributeDefinitions=attr_defs,
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"[new]  Created DynamoDB table: {name}")


def main() -> None:
    s = get_settings()
    if not s.aws_configured:
        print("ERROR: AWS is not configured. Fill AWS_* and S3_BUCKET_NAME in .env.")
        sys.exit(1)

    print(f"Region: {s.AWS_REGION}")
    ensure_bucket()
    ensure_table(
        s.DYNAMODB_USERS_TABLE,
        key_schema=[{"AttributeName": "email", "KeyType": "HASH"}],
        attr_defs=[{"AttributeName": "email", "AttributeType": "S"}],
    )
    ensure_table(
        s.DYNAMODB_TABLE_NAME,
        key_schema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "file_id", "KeyType": "RANGE"},
        ],
        attr_defs=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "file_id", "AttributeType": "S"},
        ],
    )
    print("\nDone. Your AWS resources are ready.")


if __name__ == "__main__":
    main()
