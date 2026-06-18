"""Contract model."""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    contract_no = Column(String(50), unique=True, nullable=False, index=True)
    party_a = Column(String(200), nullable=False)
    party_b = Column(String(200), nullable=False)
    amount = Column(Float, nullable=True, default=0.0)
    status = Column(String(20), nullable=False, default="draft")
    sign_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    content = Column(Text, nullable=True, default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'terminated', 'expired')",
            name="ck_contract_status",
        ),
    )

    creator = relationship("User", back_populates="contracts")
    attachments = relationship(
        "Attachment", back_populates="contract", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Contract(id={self.id}, no='{self.contract_no}', status='{self.status}')>"
