from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, approve_by_email


def test_non_admin_cannot_access_admin_routes(client):
    client.post("/auth/register", json={"email": "plain@test.local", "password": "password123"})
    approve_by_email(client, "plain@test.local")

    client.post("/auth/login", json={"email": "plain@test.local", "password": "password123"})
    resp = client.get("/admin/users")
    assert resp.status_code == 403


def test_admin_cannot_delete_own_account(admin_client):
    me = admin_client.get("/auth/me").json()
    resp = admin_client.delete(f"/admin/users/{me['id']}")
    assert resp.status_code == 400


def test_admin_can_delete_other_user(admin_client):
    admin_client.post("/auth/register", json={"email": "todelete@test.local", "password": "password123"})
    users = admin_client.get("/admin/users").json()
    target = next(u for u in users if u["email"] == "todelete@test.local")

    resp = admin_client.delete(f"/admin/users/{target['id']}")
    assert resp.status_code == 204

    users_after = admin_client.get("/admin/users").json()
    assert not any(u["email"] == "todelete@test.local" for u in users_after)


def test_delete_user_cleans_up_password_reset_requests(admin_client):
    admin_client.post("/auth/register", json={"email": "u4@test.local", "password": "password123"})
    target = approve_by_email(admin_client, "u4@test.local")
    admin_client.post("/auth/forgot-password", json={"email": "u4@test.local", "new_password": "newpassword1"})

    resp = admin_client.delete(f"/admin/users/{target['id']}")
    assert resp.status_code == 204
    assert admin_client.get("/admin/password-resets").json() == []


def test_delete_nonexistent_user_returns_404(admin_client):
    resp = admin_client.delete("/admin/users/999999")
    assert resp.status_code == 404


def test_reject_pending_reset_removed_from_pending_list(admin_client):
    admin_client.post("/auth/register", json={"email": "u6@test.local", "password": "password123"})
    approve_by_email(admin_client, "u6@test.local")
    admin_client.post("/auth/forgot-password", json={"email": "u6@test.local", "new_password": "newpassword1"})

    resets = admin_client.get("/admin/password-resets").json()
    reset_id = next(r["id"] for r in resets if r["user_email"] == "u6@test.local")
    resp = admin_client.post(f"/admin/password-resets/{reset_id}/reject")
    assert resp.status_code == 200

    resets_after = admin_client.get("/admin/password-resets").json()
    updated = next(r for r in resets_after if r["id"] == reset_id)
    assert updated["status"] == "rejected"
