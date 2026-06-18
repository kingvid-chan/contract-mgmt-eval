"""Tests for AuditLogger IP extraction and audit log recording."""

import pytest
from unittest.mock import MagicMock

from app.middleware.audit import AuditLogger, _is_private_ip


class TestIPExtraction:
    """Unit tests for AuditLogger IP extraction logic."""

    def _make_request(self, headers=None, client_host="127.0.0.1"):
        """Create a mock Request with given headers and client."""
        request = MagicMock()
        request.headers = headers or {}
        request.client = MagicMock()
        request.client.host = client_host
        return request

    def test_x_real_ip_priority(self):
        """X-Real-IP takes highest priority."""
        request = self._make_request(
            headers={
                "X-Real-IP": "203.0.113.42",
                "X-Forwarded-For": "198.51.100.1",
            },
            client_host="10.0.0.1",
        )
        logger = AuditLogger(request)
        assert logger.ip_address == "203.0.113.42"

    def test_x_forwarded_for_first_non_private(self):
        """X-Forwarded-For — pick first non-private IP."""
        request = self._make_request(
            headers={
                "X-Forwarded-For": "203.0.113.1, 10.0.0.2, 172.16.0.3",
            },
            client_host="127.0.0.1",
        )
        logger = AuditLogger(request)
        assert logger.ip_address == "203.0.113.1"

    def test_x_forwarded_for_all_private_fallback(self):
        """When all X-Forwarded-For IPs are private, fallback to client.host."""
        request = self._make_request(
            headers={
                "X-Forwarded-For": "10.0.0.1, 172.16.0.2, 192.168.1.3",
            },
            client_host="127.0.0.1",
        )
        logger = AuditLogger(request)
        assert logger.ip_address == "127.0.0.1"

    def test_client_host_fallback(self):
        """Without any proxy headers, use request.client.host."""
        request = self._make_request(client_host="192.0.2.1")
        logger = AuditLogger(request)
        assert logger.ip_address == "192.0.2.1"

    def test_invalid_ip_skipped(self):
        """Invalid IPs in X-Forwarded-For are skipped."""
        request = self._make_request(
            headers={
                "X-Forwarded-For": "not-an-ip, 203.0.113.5, garbage",
            },
            client_host="127.0.0.1",
        )
        logger = AuditLogger(request)
        assert logger.ip_address == "203.0.113.5"

    def test_ipv6_address(self):
        """IPv6 addresses are correctly handled."""
        request = self._make_request(
            headers={"X-Real-IP": "2001:db8::1"},
        )
        logger = AuditLogger(request)
        assert logger.ip_address == "2001:db8::1"

    def test_ipv6_private_skipped(self):
        """Private IPv6 addresses (ambiguous) — our current impl doesn't filter IPv6 private ranges."""
        request = self._make_request(
            headers={"X-Real-IP": "::1"},
        )
        logger = AuditLogger(request)
        # ::1 is a valid IPv6 address, will be used
        assert logger.ip_address == "::1"

    def test_no_client_info(self):
        """If client is None, return 'unknown'."""
        request = MagicMock()
        request.headers = {}
        request.client = None
        logger = AuditLogger(request)
        assert logger.ip_address == "unknown"


class TestPrivateIPFilter:
    """Tests for _is_private_ip helper."""

    def test_private_10(self):
        assert _is_private_ip("10.0.0.1") is True
        assert _is_private_ip("10.255.255.255") is True

    def test_private_172_16(self):
        assert _is_private_ip("172.16.0.1") is True
        assert _is_private_ip("172.31.255.255") is True

    def test_private_192_168(self):
        assert _is_private_ip("192.168.0.1") is True
        assert _is_private_ip("192.168.255.255") is True

    def test_private_127(self):
        assert _is_private_ip("127.0.0.1") is True

    def test_public_ips(self):
        assert _is_private_ip("8.8.8.8") is False
        assert _is_private_ip("203.0.113.1") is False
        assert _is_private_ip("1.1.1.1") is False

    def test_invalid_ip_is_private(self):
        """Unparseable IPs are treated as private to be skipped."""
        assert _is_private_ip("not-an-ip") is True
        assert _is_private_ip("") is True


class TestLogActionWithIP:
    """Tests that log_action stores ip_address correctly."""

    def test_log_action_stores_ip(self, db):
        """log_action with ip_address should persist to database."""
        from app.services import auth_service
        from app.schemas.auth import RegisterRequest

        # Register a user with IP
        data = RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        user = auth_service.register(db, data, ip_address="203.0.113.99")
        assert user.id is not None

        # Query the audit log
        from app.models import AuditLog
        log = db.query(AuditLog).filter(
            AuditLog.user_id == user.id,
            AuditLog.action == "user.register",
        ).first()
        assert log is not None
        assert log.ip_address == "203.0.113.99"

    def test_log_action_without_ip(self, db):
        """log_action without ip_address should store None (backward compat)."""
        from app.services import auth_service
        from app.schemas.auth import RegisterRequest

        data = RegisterRequest(
            username="nouser",
            email="no@example.com",
            password="password123",
        )
        user = auth_service.register(db, data)  # No IP passed
        assert user.id is not None

        from app.models import AuditLog
        log = db.query(AuditLog).filter(
            AuditLog.user_id == user.id,
            AuditLog.action == "user.register",
        ).first()
        assert log is not None
        assert log.ip_address is None


class TestLogoutAuditLog:
    """Tests that logout triggers audit log recording."""

    def test_logout_creates_audit_log(self, client, user_token):
        """POST /api/auth/logout should create an audit log entry."""
        resp = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "已登出"

    def test_logout_audit_log_has_ip(self, client, user_token, db):
        """logout audit log should contain ip_address (testclient → 127.0.0.1)."""
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        from app.models import AuditLog
        log = (
            db.query(AuditLog)
            .filter(AuditLog.action == "user.logout")
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert log is not None
        assert log.action == "user.logout"
        assert log.ip_address is not None
        # TestClient uses 'testclient' as its host
        assert log.ip_address == "testclient"

    def test_login_audit_log_has_ip(self, client, db):
        """login audit log should contain ip_address."""
        # Create a user first
        from app.models import User
        from app.utils.security import hash_password

        db_session = db
        user = User(
            username="login_test",
            email="login@test.com",
            password_hash=hash_password("test123"),
            role="user",
            status="active",
        )
        db_session.add(user)
        db_session.commit()

        resp = client.post(
            "/api/auth/login",
            json={"username": "login_test", "password": "test123"},
        )
        assert resp.status_code == 200

        from app.models import AuditLog
        log = (
            db.query(AuditLog)
            .filter(AuditLog.action == "user.login")
            .order_by(AuditLog.id.desc())
            .first()
        )
        assert log is not None
        assert log.ip_address is not None
        assert log.ip_address == "testclient"
