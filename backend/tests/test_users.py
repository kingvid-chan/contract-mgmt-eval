"""Tests for user management endpoints."""


def test_admin_list_users(client, admin_token):
    resp = client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 1
    assert data["items"][0]["username"] is not None


def test_user_cannot_list_users(client, user_token):
    resp = client.get("/api/users", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_admin_create_user(client, admin_token):
    resp = client.post(
        "/api/users",
        json={"username": "created", "email": "c@t.com", "password": "pass123", "role": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "created"
    assert data["role"] == "user"


def test_admin_create_user_duplicate(client, admin_token):
    client.post(
        "/api/users",
        json={"username": "dup2", "email": "d1@t.com", "password": "pass123", "role": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.post(
        "/api/users",
        json={"username": "dup2", "email": "d2@t.com", "password": "pass123", "role": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 409


def test_admin_get_user(client, admin_token):
    resp = client.get("/api/users/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


def test_admin_update_user(client, admin_token):
    # Create a test user first
    create = client.post(
        "/api/users",
        json={"username": "testuser2", "email": "t2@t.com", "password": "pass123", "role": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    uid = create.json()["id"]

    resp = client.put(
        f"/api/users/{uid}",
        json={"username": "updated_user", "email": "updated@t.com"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "updated_user"
    assert data["email"] == "updated@t.com"


def test_admin_toggle_user_status(client, admin_token):
    # Create a test user first
    create = client.post(
        "/api/users",
        json={"username": "toguser", "email": "tog@t.com", "password": "pass123", "role": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    uid = create.json()["id"]

    # Disable
    resp = client.patch(
        f"/api/users/{uid}/status",
        json={"status": "disabled"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "disabled"

    # Enable
    resp = client.patch(
        f"/api/users/{uid}/status",
        json={"status": "active"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_user_cannot_create_user(client, user_token):
    resp = client.post(
        "/api/users",
        json={"username": "bad", "email": "bad@t.com", "password": "pass123", "role": "user"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_get_nonexistent_user(client, admin_token):
    resp = client.get("/api/users/9999", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 404


def test_user_search(client, admin_token):
    client.post(
        "/api/users",
        json={"username": "searchable", "email": "s@t.com", "password": "pass123", "role": "user"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    resp = client.get(
        "/api/users?search=search",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_user_get_me(client, admin_token):
    resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"
