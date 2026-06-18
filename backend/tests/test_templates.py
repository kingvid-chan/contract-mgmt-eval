"""Tests for contract template management endpoints."""

from app.services.template_service import render_template_content


# ── CRUD tests ──────────────────────────────────────────────

def test_create_template_admin_success(admin_token, client):
    resp = client.post(
        "/api/templates",
        json={
            "name": "采购合同模板",
            "category": "采购",
            "party_a_default": "甲公司",
            "party_b_default": "乙公司",
            "content": "本合同由{{甲方}}与{{乙方}}签订，金额{{金额}}元。",
            "amount_min": 1000,
            "amount_max": 50000,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "采购合同模板"
    assert data["category"] == "采购"
    assert data["party_a_default"] == "甲公司"
    assert data["amount_min"] == 1000
    assert data["is_deleted"] is False


def test_create_template_non_admin_forbidden(user_token, client):
    resp = client.post(
        "/api/templates",
        json={"name": "普通用户创建的模板"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_create_template_unauthorized(client):
    resp = client.post("/api/templates", json={"name": "未登录模板"})
    assert resp.status_code == 401


def test_create_template_minimal_fields(admin_token, client):
    resp = client.post(
        "/api/templates",
        json={"name": "最简模板"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "最简模板"
    assert data["category"] == ""
    assert data["content"] == ""


# ── List templates tests ────────────────────────────────────

def test_list_templates_admin(admin_token, client):
    # Create two templates
    for i in range(3):
        client.post(
            "/api/templates",
            json={"name": f"Template-{i}", "category": "test"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    resp = client.get("/api/templates", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


def test_list_templates_user_forbidden(user_token, client):
    resp = client.get("/api/templates", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_list_templates_with_search(admin_token, client):
    client.post(
        "/api/templates",
        json={"name": "服务合同模板", "category": "服务"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    client.post(
        "/api/templates",
        json={"name": "采购合同模板", "category": "采购"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Search by name
    resp = client.get(
        "/api/templates?search=采购",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "采购合同模板"

    # Search by category
    resp = client.get(
        "/api/templates?search=服务",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.json()["total"] == 1


def test_list_templates_pagination(admin_token, client):
    for i in range(5):
        client.post(
            "/api/templates",
            json={"name": f"PageTest-{i}"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    resp = client.get(
        "/api/templates?page=1&page_size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] >= 5


def test_list_templates_excludes_deleted(admin_token, client):
    resp = client.post(
        "/api/templates",
        json={"name": "待删除模板"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    tid = resp.json()["id"]
    client.delete(f"/api/templates/{tid}", headers={"Authorization": f"Bearer {admin_token}"})

    resp = client.get("/api/templates", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(t["id"] != tid for t in items)


# ── Get template detail ─────────────────────────────────────

def test_get_template_detail(admin_token, client):
    create = client.post(
        "/api/templates",
        json={"name": "详情测试模板", "content": "测试正文"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    tid = create.json()["id"]
    resp = client.get(f"/api/templates/{tid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "详情测试模板"
    assert resp.json()["content"] == "测试正文"


def test_get_template_not_found(admin_token, client):
    resp = client.get("/api/templates/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


def test_get_template_user_forbidden(user_token, client):
    resp = client.get("/api/templates/1", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


# ── Update template ─────────────────────────────────────────

def test_update_template(admin_token, client):
    create = client.post(
        "/api/templates",
        json={"name": "旧名称", "category": "旧分类"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    tid = create.json()["id"]
    resp = client.put(
        f"/api/templates/{tid}",
        json={"name": "新名称", "category": "新分类"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "新名称"
    assert data["category"] == "新分类"


def test_update_template_not_found(admin_token, client):
    resp = client.put(
        "/api/templates/99999",
        json={"name": "不存在"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 404


# ── Soft delete ─────────────────────────────────────────────

def test_soft_delete_template(admin_token, client):
    create = client.post(
        "/api/templates",
        json={"name": "软删除测试"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    tid = create.json()["id"]

    resp = client.delete(f"/api/templates/{tid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "模板已删除"

    # Verify it's not in list
    resp = client.get("/api/templates", headers={"Authorization": f"Bearer {admin_token}"})
    items = resp.json()["items"]
    assert all(t["id"] != tid for t in items)

    # Verify it returns 404 on get
    resp = client.get(f"/api/templates/{tid}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


def test_soft_delete_not_found(admin_token, client):
    resp = client.delete("/api/templates/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


# ── Dropdown endpoint ───────────────────────────────────────

def test_dropdown_authenticated(admin_token, user_token, client):
    # Admin creates templates
    client.post(
        "/api/templates",
        json={"name": "模板A", "category": "cat-a"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    client.post(
        "/api/templates",
        json={"name": "模板B", "category": "cat-b"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Admin can access dropdown
    resp = client.get("/api/templates/dropdown", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 2

    # User can access dropdown
    resp = client.get("/api/templates/dropdown", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_dropdown_unauthorized(client):
    resp = client.get("/api/templates/dropdown")
    assert resp.status_code == 401


def test_dropdown_excludes_deleted(admin_token, user_token, client):
    # Create and delete a template
    create = client.post(
        "/api/templates",
        json={"name": "将删除的模板"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    tid = create.json()["id"]
    client.delete(f"/api/templates/{tid}", headers={"Authorization": f"Bearer {admin_token}"})

    # Dropdown should not include deleted
    resp = client.get("/api/templates/dropdown", headers={"Authorization": f"Bearer {user_token}"})
    items = resp.json()
    assert all(t["id"] != tid for t in items)


# ── Placeholder rendering unit test ─────────────────────────

def test_render_template_content():
    content = "本合同由{{甲方}}与{{乙方}}于{{日期}}签订，金额为{{金额}}元。"
    variables = {
        "甲方": "测试甲方公司",
        "乙方": "测试乙方公司",
        "日期": "2026-06-18",
        "金额": "100000",
    }
    result = render_template_content(content, variables)
    assert "{{甲方}}" not in result
    assert "测试甲方公司" in result
    assert "测试乙方公司" in result
    assert "2026-06-18" in result
    assert "100000" in result


def test_render_template_content_unknown_placeholder():
    content = "金额{{金额}}元，备注{{备注}}"
    variables = {"金额": "5000"}
    result = render_template_content(content, variables)
    assert "5000" in result
    # Unknown placeholder left unchanged
    assert "{{备注}}" in result


def test_render_template_content_no_placeholders():
    content = "普通文本，无占位符"
    result = render_template_content(content, {})
    assert result == content
