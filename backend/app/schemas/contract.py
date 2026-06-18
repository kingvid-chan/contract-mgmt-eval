"""Contract request/response schemas."""

from datetime import date, datetime
from pydantic import BaseModel, Field


class ContractCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    contract_no: str = Field(..., min_length=1, max_length=50)
    party_a: str = Field(..., min_length=1, max_length=200)
    party_b: str = Field(..., min_length=1, max_length=200)
    amount: float | None = 0.0
    sign_date: date | None = None
    expiry_date: date | None = None
    content: str = ""


class ContractUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    contract_no: str | None = Field(None, min_length=1, max_length=50)
    party_a: str | None = Field(None, min_length=1, max_length=200)
    party_b: str | None = Field(None, min_length=1, max_length=200)
    amount: float | None = None
    sign_date: date | None = None
    expiry_date: date | None = None
    content: str | None = None


class ContractStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|terminated|expired)$")


class ContractResponse(BaseModel):
    id: int
    title: str
    contract_no: str
    party_a: str
    party_b: str
    amount: float | None
    status: str
    sign_date: date | None
    expiry_date: date | None
    content: str | None
    created_by: int
    creator_username: str | None = None
    attachment_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContractListResponse(BaseModel):
    total: int
    items: list[ContractResponse]
