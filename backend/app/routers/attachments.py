"""Attachment management API endpoints."""

import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models import User
from app.schemas.attachment import AttachmentResponse, AttachmentListResponse
from app.services import attachment_service

router = APIRouter(tags=["attachments"])


@router.post(
    "/api/contracts/{contract_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_attachment(
    contract_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an attachment (PDF/Word, ≤10MB)."""
    return attachment_service.upload_attachment(db, contract_id, file, current_user)


@router.get(
    "/api/contracts/{contract_id}/attachments",
    response_model=AttachmentListResponse,
)
def list_attachments(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all attachments for a contract."""
    return attachment_service.list_attachments(db, contract_id, current_user)


@router.get(
    "/api/attachments/{attachment_id}/download",
)
def download_attachment(
    attachment_id: int,
    preview: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download or preview an attachment file."""
    from app.services.attachment_service import _check_attachment_ownership

    attachment = _check_attachment_ownership(db, attachment_id, current_user)

    if not os.path.exists(attachment.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    disposition = "inline" if preview else "attachment"
    media_type_map = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    media_type = media_type_map.get(attachment.file_type, "application/octet-stream")

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_name,
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{attachment.original_name}"'},
    )


@router.delete("/api/attachments/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an attachment."""
    attachment_service.delete_attachment(db, attachment_id, current_user)
    return {"message": "附件已删除"}
