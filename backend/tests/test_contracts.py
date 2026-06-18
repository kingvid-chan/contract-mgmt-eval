"""Tests for contract management endpoints."""

from datetime import date


def test_create_contract(admin_token, client):
    resp = client.post(
        "/api/contracts",
        json={"title": "测试合同", "contract_no": "TEST-001", "party_a": "甲方", "party_b": "乙方", "amount": 10000},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["contract_no"] == "TEST-001"


def test_create_contract_duplicate_no(admin_token, client):
    client.post(
        "/api/contracts",
        json={"title": "C1", "contract_no": "DUP-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.post(
        "/api/contracts",
        json={"title": "C2", "contract_no": "DUP-001", "party_a": "C", "party_b": "D"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 409


def test_list_contracts_admin(admin_token, client):
    """Admin sees all contracts."""
    client.post(
        "/api/contracts",
        json={"title": "Admin contract", "contract_no": "A-001", "party_a": "A1", "party_b": "B1"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.get("/api/contracts", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_list_contracts_user_isolation(admin_token, user_token, client):
    """Regular user sees only own contracts."""
    # Admin creates
    client.post(
        "/api/contracts",
        json={"title": "Admin's", "contract_no": "ISO-001", "party_a": "A1", "party_b": "B1"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # User creates
    client.post(
        "/api/contracts",
        json={"title": "User's", "contract_no": "ISO-002", "party_a": "A2", "party_b": "B2"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    # Admin sees 2
    resp = client.get("/api/contracts", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.json()["total"] >= 2

    # User sees only their own
    resp = client.get("/api/contracts", headers={"Authorization": f"Bearer {user_token}"})
    items = resp.json()["items"]
    assert all(c["created_by"] == 2 for c in items)  # user has id=2


def test_get_contract(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Detail", "contract_no": "DET-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    resp = client.get(f"/api/contracts/{cid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Detail"


def test_user_cannot_access_other_contract(admin_token, user_token, client):
    """User cannot access admin's contract."""
    create = client.post(
        "/api/contracts",
        json={"title": "Private", "contract_no": "PRIV-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    resp = client.get(f"/api/contracts/{cid}", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_update_contract(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Old title", "contract_no": "UPD-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    resp = client.put(
        f"/api/contracts/{cid}",
        json={"title": "New title"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"


def test_delete_draft_contract(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "To delete", "contract_no": "DEL-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    resp = client.delete(f"/api/contracts/{cid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "合同已删除"


def test_cannot_delete_active_contract(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Keep", "contract_no": "NO-DEL-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    # Activate
    client.patch(
        f"/api/contracts/{cid}/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.delete(f"/api/contracts/{cid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 400


def test_status_flow_draft_to_active(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Flow", "contract_no": "FLOW-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    resp = client.patch(
        f"/api/contracts/{cid}/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_status_flow_active_to_terminated(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Term", "contract_no": "TERM-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    client.patch(
        f"/api/contracts/{cid}/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.patch(
        f"/api/contracts/{cid}/status",
        json={"status": "terminated"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "terminated"


def test_invalid_transition(admin_token, client):
    """Cannot jump from draft to terminated."""
    create = client.post(
        "/api/contracts",
        json={"title": "Bad", "contract_no": "BAD-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]
    resp = client.patch(
        f"/api/contracts/{cid}/status",
        json={"status": "terminated"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400
    assert "不允许" in resp.json()["detail"]


def test_search_contracts(admin_token, client):
    client.post(
        "/api/contracts",
        json={"title": "UniqueTitle", "contract_no": "SRCH-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.get(
        "/api/contracts?search=Unique",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_filter_by_status(admin_token, client):
    client.post(
        "/api/contracts",
        json={"title": "Drafty", "contract_no": "FIL-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.get(
        "/api/contracts?status=draft",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    for c in resp.json()["items"]:
        assert c["status"] == "draft"


def test_pagination(admin_token, client):
    for i in range(5):
        client.post(
            "/api/contracts",
            json={"title": f"P{i}", "contract_no": f"PAG-{i:03d}", "party_a": "A", "party_b": "B"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    resp = client.get(
        "/api/contracts?page=1&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) <= 2


def test_contract_audit_log_ip(admin_token, client):
    """Contract CRUD should record ip_address in audit log."""
    from app.models import AuditLog, Contract
    from tests.conftest import TestSessionLocal

    # Create contract
    resp = client.post(
        "/api/contracts",
        json={"title": "Audit Contract", "contract_no": "AUDIT-C-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    cid = resp.json()["id"]

    # Update contract
    resp = client.put(
        f"/api/contracts/{cid}",
        json={"title": "Audit Contract Updated"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # Status change (draft → active)
    resp = client.patch(
        f"/api/contracts/{cid}/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # Verify audit logs have ip_address
    db = TestSessionLocal()
    for action in ["contract.create", "contract.update", "contract.status_change"]:
        log = db.query(AuditLog).filter(
            AuditLog.action == action,
            AuditLog.target_id == cid,
        ).first()
        assert log is not None, f"Expected audit log for {action}"
        assert log.ip_address is not None, f"Expected ip_address for {action}"
    db.close()
