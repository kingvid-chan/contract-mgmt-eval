"""ContractTemplate model."""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ContractTemplate(Base):
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, default="")
    party_a_default = Column(String(200), nullable=True)
    party_b_default = Column(String(200), nullable=True)
    content = Column(Text, nullable=False, default="")
    amount_min = Column(Float, nullable=True)
    amount_max = Column(Float, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    creator = relationship("User")

    def __repr__(self):
        return f"<ContractTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"
