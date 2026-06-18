"""Attachment management business logic."""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Attachment, Contract, User
from app.utils.audit import log_action


def _check_contract_ownership(db: Session, contract_id: int, user: User) -> Contract:
    """Get contract and verify ownership. Raises HTTPException on failure."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if user.role != "admin" and contract.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此合同的附件")
    return contract


def _check_attachment_ownership(db: Session, attachment_id: int, user: User) -> Attachment:
    """Get attachment and verify contract ownership. Raises on failure."""
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")

    contract = db.query(Contract).filter(Contract.id == attachment.contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if user.role != "admin" and contract.created_by != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此附件")

    return attachment


def validate_file(file: UploadFile) -> None:
    """Validate file type and size. Raises HTTPException on failure."""
    # Check extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件格式: {ext}。仅支持 PDF 和 Word 文档",
        )

    # Check MIME type (if available)
    if file.content_type and file.content_type not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}",
        )


def upload_attachment(
    db: Session, contract_id: int, file: UploadFile, user: User
) -> Attachment:
    """Upload and store an attachment file."""
    _check_contract_ownership(db, contract_id, user)
    validate_file(file)

    # Read file content
    content = file.file.read()
    file_size = len(content)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE // (1024*1024)}MB)",
        )

    # Generate unique filename
    ext = Path(file.filename or ".bin").suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_name)

    # Write to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    # Record in database
    attachment = Attachment(
        contract_id=contract_id,
        filename=stored_name,
        original_name=file.filename or "unknown",
        file_type=ext.lstrip("."),
        file_size=file_size,
        file_path=file_path,
        uploaded_by=user.id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    log_action(db, user.id, "attachment.upload", "attachment", attachment.id,
               f"Uploaded {attachment.original_name} ({file_size} bytes)")

    # Eager load uploader
    _ = attachment.uploader
    return attachment


def list_attachments(db: Session, contract_id: int, user: User) -> dict:
    """List all attachments for a contract."""
    _check_contract_ownership(db, contract_id, user)

    items = (
        db.query(Attachment)
        .filter(Attachment.contract_id == contract_id)
        .order_by(Attachment.uploaded_at.desc())
        .all()
    )

    result = []
    for a in items:
        result.append({
            "id": a.id,
            "contract_id": a.contract_id,
            "filename": a.filename,
            "original_name": a.original_name,
            "file_type": a.file_type,
            "file_size": a.file_size,
            "uploaded_by": a.uploaded_by,
            "uploader_username": a.uploader.username if a.uploader else None,
            "uploaded_at": a.uploaded_at,
        })

    return {"total": len(result), "items": result}


def delete_attachment(db: Session, attachment_id: int, user: User) -> None:
    """Delete an attachment (record + file on disk)."""
    attachment = _check_attachment_ownership(db, attachment_id, user)

    # Remove file from disk
    try:
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
    except OSError:
        pass  # File already gone, continue deleting the DB record

    db.delete(attachment)
    db.commit()

    log_action(db, user.id, "attachment.delete", "attachment", attachment_id,
               f"Deleted attachment {attachment.original_name}")
