"""Attachment request/response schemas."""

from datetime import datetime
from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: int
    contract_id: int
    filename: str
    original_name: str
    file_type: str
    file_size: int
    uploaded_by: int
    uploader_username: str | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class AttachmentListResponse(BaseModel):
    total: int
    items: list[AttachmentResponse]
