"""Tests for attachment management endpoints."""

import io


def test_upload_attachment(admin_token, client):
    # Create a contract first
    create = client.post(
        "/api/contracts",
        json={"title": "With attachment", "contract_no": "ATT-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    pdf_content = io.BytesIO(b"%PDF-1.4 fake pdf content")
    resp = client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["original_name"] == "test.pdf"
    assert data["file_type"] == "pdf"
    assert data["contract_id"] == cid


def test_upload_invalid_type(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Bad type", "contract_no": "TYP-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    txt_content = io.BytesIO(b"not a pdf")
    resp = client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("test.txt", txt_content, "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400
    assert "不支持" in resp.json()["detail"]


def test_list_attachments(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "List atts", "contract_no": "LST-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    # Upload 2 files
    for name in ["a.pdf", "b.docx"]:
        ext = name.split(".")[1]
        client.post(
            f"/api/contracts/{cid}/attachments",
            files={"file": (name, io.BytesIO(b"x" * 10), f"application/{'pdf' if ext == 'pdf' else 'vnd.openxmlformats-officedocument.wordprocessingml.document'}")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    resp = client.get(
        f"/api/contracts/{cid}/attachments",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_download_attachment(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Download", "contract_no": "DL-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    upload = client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("down.pdf", io.BytesIO(b"download me"), "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    aid = upload.json()["id"]

    resp = client.get(f"/api/attachments/{aid}/download?token={admin_token}")
    assert resp.status_code == 200
    assert resp.headers["content-disposition"].startswith("attachment")


def test_download_with_header_auth(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "DL2", "contract_no": "DL-002", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    upload = client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("d2.pdf", io.BytesIO(b"x"), "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    aid = upload.json()["id"]

    resp = client.get(
        f"/api/attachments/{aid}/download",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200


def test_preview_attachment(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Preview", "contract_no": "PRE-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    upload = client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("prev.pdf", io.BytesIO(b"preview me"), "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    aid = upload.json()["id"]

    resp = client.get(f"/api/attachments/{aid}/download?token={admin_token}&preview=true")
    assert resp.status_code == 200
    assert "inline" in resp.headers["content-disposition"]


def test_delete_attachment(admin_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Del att", "contract_no": "DELA-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    upload = client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("del.pdf", io.BytesIO(b"delete me"), "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    aid = upload.json()["id"]

    resp = client.delete(f"/api/attachments/{aid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "附件已删除"

    # Verify gone
    resp = client.get(
        f"/api/attachments/{aid}/download?token={admin_token}"
    )
    assert resp.status_code == 404


def test_user_cannot_access_admin_attachments(admin_token, user_token, client):
    create = client.post(
        "/api/contracts",
        json={"title": "Admin only", "contract_no": "ADM-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    # Upload as admin
    client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("admin.pdf", io.BytesIO(b"admin file"), "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # User tries to list
    resp = client.get(
        f"/api/contracts/{cid}/attachments",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_upload_to_nonexistent_contract(admin_token, client):
    resp = client.post(
        "/api/contracts/9999/attachments",
        files={"file": ("x.pdf", io.BytesIO(b"x"), "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


def test_attachment_audit_log_ip(admin_token, client):
    """Attachment upload/delete should record ip_address in audit log."""
    from app.models import AuditLog
    from tests.conftest import TestSessionLocal
    import io

    # Create contract
    create = client.post(
        "/api/contracts",
        json={"title": "Audit Att", "contract_no": "AUDIT-A-001", "party_a": "A", "party_b": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cid = create.json()["id"]

    # Upload attachment
    upload = client.post(
        f"/api/contracts/{cid}/attachments",
        files={"file": ("audit.pdf", io.BytesIO(b"audit file"), "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code == 201
    aid = upload.json()["id"]

    # Delete attachment
    resp = client.delete(
        f"/api/attachments/{aid}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # Verify audit logs have ip_address
    db = TestSessionLocal()
    for action, target_id in [("attachment.upload", aid), ("attachment.delete", aid)]:
        log = db.query(AuditLog).filter(
            AuditLog.action == action,
            AuditLog.target_id == target_id,
        ).first()
        assert log is not None, f"Expected audit log for {action}"
        assert log.ip_address is not None, f"Expected ip_address for {action}"
    db.close()
