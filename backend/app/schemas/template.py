"""ContractTemplate request/response schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = ""
    party_a_default: str | None = None
    party_b_default: str | None = None
    content: str = ""
    amount_min: float | None = None
    amount_max: float | None = None


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = None
    party_a_default: str | None = None
    party_b_default: str | None = None
    content: str | None = None
    amount_min: float | None = None
    amount_max: float | None = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    category: str
    party_a_default: str | None
    party_b_default: str | None
    content: str | None
    amount_min: float | None
    amount_max: float | None
    is_deleted: bool
    created_by: int
    creator_username: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    total: int
    items: list[TemplateResponse]


class TemplateDropdownItem(BaseModel):
    id: int
    name: str
    category: str
