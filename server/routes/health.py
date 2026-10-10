"""Health-check route — confirms the backend is alive and if AWS is configured."""
from datetime import datetime, timezone

from fastapi import APIRouter

from server.config import get_settings
from server.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="aws-cloud-backup-api",
        aws_configured=settings.aws_configured,
        region=settings.AWS_REGION,
        time=datetime.now(timezone.utc).isoformat(),
    )
