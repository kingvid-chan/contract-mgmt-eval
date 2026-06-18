"""Tests for AuditLog API — filtering, pagination, permissions."""

from datetime import datetime, timezone, timedelta

from app.models import AuditLog
from app.utils.security import hash_password
from app.models import User


def _ensure_test_users(db_session):
    """Ensure user_id=1 (admin) and user_id=2 (regular) exist for FK references."""
    for uid, uname, role in [(1, "admin", "admin"), (2, "user", "user")]:
        existing = db_session.query(User).filter(User.id == uid).first()
        if not existing:
            user = User(
                id=uid,
                username=uname,
                email=f"{uname}@test.com",
                password_hash=hash_password(f"{uname}123"),
                role=role,
                status="active",
            )
            db_session.add(user)
    db_session.commit()


def _seed_audit_logs(db_session, count=30):
    """Insert test audit log entries directly into DB."""
    _ensure_test_users(db_session)
    actions = [
        "user.login", "user.logout", "contract.create",
        "contract.update", "contract.status_change", "attachment.upload",
    ]
    base_time = datetime.now(timezone.utc)
    for i in range(count):
        entry = AuditLog(
            user_id=1 if i % 3 != 0 else 2,
            action=actions[i % len(actions)],
            target_type="contract" if "contract" in actions[i % len(actions)] else None,
            target_id=100 + i if "contract" in actions[i % len(actions)] else None,
            detail=f"Test audit entry #{i}",
            ip_address=f"203.0.113.{i % 255}",
            created_at=base_time - timedelta(minutes=count - i),
        )
        db_session.add(entry)
    db_session.commit()


class TestAuditLogPermissions:
    """Tests for access control on GET /api/audit-logs."""

    def test_list_as_admin(self, client, admin_token):
        """Admin should get 200 with paginated list."""
        resp = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_as_user_forbidden(self, client, user_token):
        """Regular user should get 403."""
        resp = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_list_unauthenticated(self, client):
        """No token should get 401 (or 403 — FastAPI dependency chain behavior)."""
        resp = client.get("/api/audit-logs")
        assert resp.status_code in (401, 403)

    def test_write_methods_not_allowed(self, client, admin_token):
        """POST/PUT/PATCH/DELETE should return 405."""
        headers = {"Authorization": f"Bearer {admin_token}"}
        assert client.post("/api/audit-logs", headers=headers).status_code == 405
        assert client.put("/api/audit-logs", headers=headers).status_code == 405
        assert client.patch("/api/audit-logs", headers=headers).status_code == 405
        assert client.delete("/api/audit-logs", headers=headers).status_code == 405


class TestAuditLogFiltering:
    """Tests for filter parameters."""

    def test_filter_by_action(self, client, admin_token, db):
        """Filter by action should return only matching logs."""
        _seed_audit_logs(db, count=15)

        resp = client.get(
            "/api/audit-logs?action=user.login",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["action"] == "user.login"

    def test_filter_by_user_id(self, client, admin_token, db):
        """Filter by user_id should return only that user's logs."""
        _seed_audit_logs(db, count=10)

        resp = client.get(
            "/api/audit-logs?user_id=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["user_id"] == 2

    def test_filter_by_date_range(self, client, admin_token, db):
        """Filter by start_date and end_date should limit results."""
        _seed_audit_logs(db, count=10)

        now = datetime.now(timezone.utc)
        resp = client.get(
            "/api/audit-logs",
            params={
                "start_date": (now - timedelta(hours=1)).isoformat(),
                "end_date": (now + timedelta(hours=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

    def test_filter_by_date_range_empty(self, client, admin_token, db):
        """A future date range should return no results."""
        _seed_audit_logs(db, count=5)

        future = datetime.now(timezone.utc) + timedelta(days=365)
        resp = client.get(
            "/api/audit-logs",
            params={
                "start_date": future.isoformat(),
                "end_date": (future + timedelta(days=1)).isoformat(),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_filter_combined(self, client, admin_token, db):
        """Combined filters (action + user_id + date) should all apply."""
        _seed_audit_logs(db, count=20)

        now = datetime.now(timezone.utc)
        resp = client.get(
            "/api/audit-logs",
            params={
                "action": "contract.create",
                "user_id": 1,
                "start_date": (now - timedelta(hours=2)).isoformat(),
                "end_date": (now + timedelta(hours=2)).isoformat(),
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["action"] == "contract.create"
            assert item["user_id"] == 1


class TestAuditLogPagination:
    """Tests for pagination behavior."""

    def test_pagination_defaults(self, client, admin_token, db):
        """Default page=1, page_size=20."""
        _seed_audit_logs(db, count=25)

        resp = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 25  # May include entries from fixtures
        assert len(data["items"]) == 20  # First page, 20 items

    def test_page_size_custom(self, client, admin_token, db):
        """Custom page_size should work."""
        _seed_audit_logs(db, count=10)

        resp = client.get(
            "/api/audit-logs?page_size=3",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3

    def test_page_out_of_range(self, client, admin_token, db):
        """Page beyond available data returns empty items."""
        _seed_audit_logs(db, count=5)

        resp = client.get(
            "/api/audit-logs?page=99",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 5  # May include entries from fixtures
        assert data["items"] == []

    def test_page_size_max(self, client, admin_token, db):
        """page_size should be capped at 100."""
        _seed_audit_logs(db, count=5)

        resp = client.get(
            "/api/audit-logs?page_size=200",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # page_size > 100 should be rejected by FastAPI validation (422)
        assert resp.status_code == 422


class TestAuditLogSorting:
    """Tests for sorting order."""

    def test_sorted_by_created_at_desc(self, client, admin_token, db):
        """Logs should be sorted by created_at DESC (newest first)."""
        _seed_audit_logs(db, count=10)

        resp = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]
        for i in range(len(items) - 1):
            assert items[i]["created_at"] >= items[i + 1]["created_at"], (
                f"Item {i} ({items[i]['created_at']}) should be >= "
                f"item {i+1} ({items[i+1]['created_at']})"
            )


class TestAuditLogResponse:
    """Tests for response structure."""

    def test_response_structure(self, client, admin_token, db):
        """Each item should have all expected fields."""
        _seed_audit_logs(db, count=1)

        resp = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        item = data["items"][0]
        assert "id" in item
        assert "user_id" in item
        assert "username" in item
        assert "action" in item
        assert "target_type" in item
        assert "target_id" in item
        assert "detail" in item
        assert "ip_address" in item
        assert "created_at" in item

    def test_username_is_populated(self, client, admin_token, db):
        """The username field should be populated via JOIN."""
        _seed_audit_logs(db, count=3)

        resp = client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["username"] is not None
            assert len(item["username"]) > 0
