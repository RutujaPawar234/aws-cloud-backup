"""
Central configuration loaded from environment variables (.env file).

No secret is hard-coded here. Boto3 picks up AWS credentials from the same
environment variables, so the same code runs locally and on Render unchanged.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings read once from the environment."""

    def __init__(self) -> None:
        # --- AWS ---
        self.AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
        self.S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
        self.DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "BackupFiles")
        self.DYNAMODB_USERS_TABLE: str = os.getenv("DYNAMODB_USERS_TABLE", "BackupUsers")

        # --- Auth / JWT ---
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-insecure-change-me")
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720")
        )

        # Max upload size (bytes). Default 50 MB.
        self.MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))

    @property
    def aws_configured(self) -> bool:
        """True only when the server has the AWS settings it needs."""
        return bool(
            self.AWS_ACCESS_KEY_ID
            and self.AWS_SECRET_ACCESS_KEY
            and self.S3_BUCKET_NAME
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read the environment only once)."""
    return Settings()
