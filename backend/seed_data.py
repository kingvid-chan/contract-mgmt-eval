"""Seed the database with demo accounts and sample contracts."""

import os
import sys
from datetime import date

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, init_db
from app.models import User, Contract, AuditLog
from passlib.hash import bcrypt


def seed():
    """Create tables and insert seed data."""
    print("Creating tables...")
    init_db()

    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter_by(username="admin").first()
        if existing_admin:
            print("Seed data already exists. Skipping.")
            return

        # Demo users
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=bcrypt.hash("admin123"),
            role="admin",
            status="active",
        )
        user = User(
            username="user",
            email="user@example.com",
            password_hash=bcrypt.hash("user123"),
            role="user",
            status="active",
        )
        db.add_all([admin, user])
        db.flush()  # get IDs

        # Sample contracts (created by admin)
        contracts = [
            Contract(
                title="2026年度办公用品采购合同",
                contract_no="HT-2026-001",
                party_a="ABC科技有限公司",
                party_b="XYZ贸易有限公司",
                amount=150000.00,
                status="active",
                sign_date=date(2026, 1, 15),
                expiry_date=date(2026, 12, 31),
                content="办公用品年度采购框架协议，包含文具、耗材等。",
                created_by=admin.id,
            ),
            Contract(
                title="软件开发服务合同",
                contract_no="HT-2026-002",
                party_a="DEF信息技术有限公司",
                party_b="GHI数据服务有限公司",
                amount=500000.00,
                status="draft",
                sign_date=None,
                expiry_date=None,
                content="企业数据中台定制开发，含需求分析、设计、开发、测试、部署。",
                created_by=user.id,
            ),
            Contract(
                title="2025年办公场地租赁合同",
                contract_no="HT-2025-003",
                party_a="JKL房地产有限公司",
                party_b="ABC科技有限公司",
                amount=360000.00,
                status="terminated",
                sign_date=date(2025, 3, 1),
                expiry_date=date(2026, 2, 28),
                content="办公场地租赁，面积500平方米，含物业费。",
                created_by=admin.id,
            ),
        ]
        db.add_all(contracts)
        db.flush()

        # Audit log for seed
        audit = AuditLog(
            user_id=admin.id,
            action="system.seed",
            target_type="system",
            detail="Database seeded with demo accounts and sample contracts",
        )
        db.add(audit)

        db.commit()
        print("Seed data inserted successfully.")
        print(f"  Users: admin/admin123, user/user123")
        print(f"  Contracts: {len(contracts)} sample records")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
