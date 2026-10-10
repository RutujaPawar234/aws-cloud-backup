"""File backup routes: upload, list, detail, download, delete. All need a token."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from server.config import get_settings
from server.models.schemas import FileMetadata, MessageResponse, UploadResponse
# Metadata backend: S3-backed (works everywhere). Swap this single import to
# `dynamodb_service` if your AWS account allows DynamoDB and you prefer it.
from server.services import metadata_service as dynamodb_service
from server.services import s3_service
from server.utils.dependencies import get_current_user

router = APIRouter(prefix="/files", tags=["files"])


def _cloud_error(detail: str = "Cloud storage error. Please try again.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
) -> UploadResponse:
    """Upload a file to Amazon S3 and record metadata in DynamoDB."""
    settings = get_settings()
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="The selected file is empty.")
    if len(contents) > settings.MAX_FILE_SIZE:
        mb = settings.MAX_FILE_SIZE // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"File too large. Max {mb} MB.")

    file_name = file.filename or "untitled"
    ext = file_name.rsplit(".", 1)[-1].upper() if "." in file_name else "FILE"
    s3_key = s3_service.build_s3_key(user["id"], file_name)

    try:
        s3_service.upload_file_to_s3(
            s3_key, contents, file.content_type or "application/octet-stream"
        )
        meta = dynamodb_service.save_file_metadata(
            user_id=user["id"],
            file_name=file_name,
            file_size=len(contents),
            file_type=ext,
            s3_key=s3_key,
        )
    except RuntimeError:
        raise _cloud_error("Cloud service is not configured.")
    except Exception:
        # roll back the S3 object if metadata failed, so we don't orphan it
        try:
            s3_service.delete_file_from_s3(s3_key)
        except Exception:
            pass
        raise _cloud_error("Upload failed. Please try again.")

    return UploadResponse(message="Backup completed successfully.", file=FileMetadata(**meta))


@router.get("", response_model=list[FileMetadata])
async def list_my_files(user: dict = Depends(get_current_user)) -> list[FileMetadata]:
    """List every backup belonging to the logged-in user."""
    try:
        rows = dynamodb_service.list_user_files(user["id"])
    except RuntimeError:
        raise _cloud_error("Cloud service is not configured.")
    except Exception:
        raise _cloud_error("Could not load your backups.")
    return [FileMetadata(**r) for r in rows]


@router.get("/{file_id}", response_model=FileMetadata)
async def file_detail(file_id: str, user: dict = Depends(get_current_user)) -> FileMetadata:
    """Return metadata for one of the user's files."""
    meta = dynamodb_service.get_file_metadata(user["id"], file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileMetadata(**meta)


@router.get("/{file_id}/download")
async def download(file_id: str, user: dict = Depends(get_current_user)):
    """Stream a user's file back from S3 so the client can restore it."""
    meta = dynamodb_service.get_file_metadata(user["id"], file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        data = s3_service.download_file_from_s3(meta["s3_key"])
    except RuntimeError:
        raise _cloud_error("Cloud service is not configured.")
    except Exception:
        raise _cloud_error("Download failed. Please try again.")

    headers = {"Content-Disposition": f'attachment; filename="{meta["file_name"]}"'}
    return StreamingResponse(
        io.BytesIO(data), media_type="application/octet-stream", headers=headers
    )


@router.delete("/{file_id}", response_model=MessageResponse)
async def delete(file_id: str, user: dict = Depends(get_current_user)) -> MessageResponse:
    """Delete a user's cloud backup (S3 object + DynamoDB row). Local file untouched."""
    meta = dynamodb_service.get_file_metadata(user["id"], file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found.")
    try:
        s3_service.delete_file_from_s3(meta["s3_key"])
        dynamodb_service.delete_file_metadata(user["id"], file_id)
    except RuntimeError:
        raise _cloud_error("Cloud service is not configured.")
    except Exception:
        raise _cloud_error("Delete failed. Please try again.")
    return MessageResponse(message="Cloud backup deleted.")
