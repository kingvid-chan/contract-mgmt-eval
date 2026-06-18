"""Shared test fixtures."""

import os
import sys
import pytest
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.utils.security import hash_password

# In-memory SQLite for tests
TEST_DB_URL = "sqlite:///file::memory:?cache=shared"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})


@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    """Direct database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_token(client):
    """Create admin user and return their token."""
    db = TestSessionLocal()
    admin = User(
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        role="admin",
        status="active",
    )
    db.add(admin)
    db.commit()

    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    db.close()
    return resp.json()["access_token"]


@pytest.fixture
def user_token(client):
    """Create regular user and return their token."""
    db = TestSessionLocal()
    user = User(
        username="user",
        email="user@test.com",
        password_hash=hash_password("user123"),
        role="user",
        status="active",
    )
    db.add(user)
    db.commit()

    resp = client.post("/api/auth/login", json={"username": "user", "password": "user123"})
    db.close()
    return resp.json()["access_token"]
