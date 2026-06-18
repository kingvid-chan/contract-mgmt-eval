"""Tests for authentication endpoints."""

from tests.conftest import TestSessionLocal


def test_register_success(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "newuser", "email": "new@test.com", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["role"] == "user"
    assert data["status"] == "active"
    assert "password" not in data


def test_register_duplicate_username(client):
    client.post("/api/auth/register", json={"username": "dup", "email": "a@t.com", "password": "pass123"})
    resp = client.post("/api/auth/register", json={"username": "dup", "email": "b@t.com", "password": "pass123"})
    assert resp.status_code == 409
    assert "用户名已存在" in resp.json()["detail"]


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={"username": "u1", "email": "dup@test.com", "password": "pass123"})
    resp = client.post("/api/auth/register", json={"username": "u2", "email": "dup@test.com", "password": "pass123"})
    assert resp.status_code == 409
    assert "邮箱已被注册" in resp.json()["detail"]


def test_register_short_password(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "u", "email": "u@t.com", "password": "12"},
    )
    assert resp.status_code == 422


def test_login_success(client, admin_token):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password(client, admin_token):
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401
    assert "用户名或密码错误" in resp.json()["detail"]


def test_login_nonexistent_user(client):
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


def test_me_with_token(client, admin_token):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"
    assert resp.json()["role"] == "admin"


def test_me_without_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 403


def test_me_with_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


def test_logout(client, admin_token):
    resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "已登出"


def test_password_reset(client, admin_token):
    resp = client.post("/api/auth/password-reset", json={"email": "admin@test.com"})
    assert resp.status_code == 200
    assert "message" in resp.json()
    assert "new_password" in resp.json()


def test_password_reset_nonexistent(client):
    resp = client.post("/api/auth/password-reset", json={"email": "no@test.com"})
    assert resp.status_code == 404


def test_login_audit_log_with_ip(client):
    """Login should create an audit log entry with ip_address."""
    # Register first
    client.post("/api/auth/register", json={
        "username": "audittest", "email": "audit@test.com", "password": "test1234"
    })
    resp = client.post("/api/auth/login", json={
        "username": "audittest", "password": "test1234"
    })
    assert resp.status_code == 200

    from app.models import AuditLog
    db = TestSessionLocal()
    log = db.query(AuditLog).filter(
        AuditLog.action == "user.login",
    ).order_by(AuditLog.id.desc()).first()
    db.close()
    assert log is not None
    assert log.ip_address is not None


def test_logout_audit_log_with_ip(client, user_token):
    """Logout should create an audit log entry with ip_address."""
    client.post("/api/auth/logout", headers={
        "Authorization": f"Bearer {user_token}"
    })

    from app.models import AuditLog
    db = TestSessionLocal()
    log = db.query(AuditLog).filter(
        AuditLog.action == "user.logout"
    ).order_by(AuditLog.id.desc()).first()
    db.close()
    assert log is not None
    assert log.ip_address is not None


def test_disabled_user_login(client, user_token):
    from app.models import User

    # Disable the user directly
    db_session = TestSessionLocal()
    u = db_session.query(User).filter_by(username="user").first()
    u.status = "disabled"
    db_session.commit()
    db_session.close()

    resp = client.post("/api/auth/login", json={"username": "user", "password": "user123"})
    assert resp.status_code == 401
    assert "禁用" in resp.json()["detail"]
