"""Attachment management API endpoints."""

import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, security_scheme
from app.middleware.audit import AuditLogger
from app.models import User
from app.schemas.attachment import AttachmentResponse, AttachmentListResponse
from app.services import attachment_service
from app.utils.security import decode_access_token

router = APIRouter(tags=["attachments"])


def get_current_user_optional(
    token: str | None = Query(None),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Auth via Bearer header or ?token= query param (for <a> downloads)."""
    resolved = token
    if not resolved and authorization and authorization.startswith("Bearer "):
        resolved = authorization.removeprefix("Bearer ")

    if not resolved:
        raise HTTPException(status_code=401, detail="未认证")

    payload = decode_access_token(resolved)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    user_id_str = payload.get("sub")
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.status == "disabled":
        raise HTTPException(status_code=403, detail="账户已被禁用")
    return user


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
    audit: AuditLogger = Depends(),
):
    """Upload an attachment (PDF/Word, ≤10MB)."""
    return attachment_service.upload_attachment(db, contract_id, file, current_user, ip_address=audit.ip_address)


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
    current_user: User = Depends(get_current_user_optional),
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
    audit: AuditLogger = Depends(),
):
    """Delete an attachment."""
    attachment_service.delete_attachment(db, attachment_id, current_user, ip_address=audit.ip_address)
    return {"message": "附件已删除"}
