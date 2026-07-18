from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD, approve_by_email


def test_register_creates_pending_user(client):
    resp = client.post("/auth/register", json={"email": "user@test.local", "password": "password123"})
    assert resp.status_code == 201
    assert "administrateur" in resp.json()["message"].lower()


def test_register_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "dup@test.local", "password": "password123"})
    resp = client.post("/auth/register", json={"email": "dup@test.local", "password": "autremdp1"})
    assert resp.status_code == 400


def test_login_blocked_while_pending(client):
    client.post("/auth/register", json={"email": "pending@test.local", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "pending@test.local", "password": "password123"})
    assert resp.status_code == 403
    assert "attente" in resp.json()["detail"].lower()


def test_login_wrong_password_rejected(client):
    resp = client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-password"})
    assert resp.status_code == 401


def test_login_unknown_email_rejected(client):
    resp = client.post("/auth/login", json={"email": "doesnotexist@test.local", "password": "whatever123"})
    assert resp.status_code == 401


def test_login_success_after_approval(client):
    client.post("/auth/register", json={"email": "approved@test.local", "password": "password123"})
    approve_by_email(client, "approved@test.local")
    resp = client.post("/auth/login", json={"email": "approved@test.local", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "approved@test.local"


def test_login_blocked_after_rejection(client):
    client.post("/auth/register", json={"email": "rejected@test.local", "password": "password123"})
    client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    users = client.get("/admin/users").json()
    target = next(u for u in users if u["email"] == "rejected@test.local")
    client.post(f"/admin/users/{target['id']}/reject")

    resp = client.post("/auth/login", json={"email": "rejected@test.local", "password": "password123"})
    assert resp.status_code == 403
    assert "refus" in resp.json()["detail"].lower()


def test_me_requires_authentication(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(admin_client):
    resp = admin_client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == ADMIN_EMAIL


def test_logout_clears_session(admin_client):
    resp = admin_client.post("/auth/logout")
    assert resp.status_code == 200
    resp2 = admin_client.get("/auth/me")
    assert resp2.status_code == 401


def test_protected_endpoint_requires_login(client):
    resp = client.get("/liens")
    assert resp.status_code == 401


def test_forgot_password_creates_reset_request_for_approved_user(client):
    client.post("/auth/register", json={"email": "forgot@test.local", "password": "oldpassword1"})
    approve_by_email(client, "forgot@test.local")

    resp = client.post("/auth/forgot-password", json={"email": "forgot@test.local", "new_password": "newpassword1"})
    assert resp.status_code == 200

    resets = client.get("/admin/password-resets").json()
    assert any(r["user_email"] == "forgot@test.local" and r["status"] == "pending" for r in resets)


def test_forgot_password_silent_for_unknown_email(client):
    resp = client.post("/auth/forgot-password", json={"email": "ghost@test.local", "new_password": "whatever12"})
    assert resp.status_code == 200

    client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert client.get("/admin/password-resets").json() == []


def test_old_password_still_valid_until_reset_approved(client):
    client.post("/auth/register", json={"email": "u2@test.local", "password": "oldpassword1"})
    approve_by_email(client, "u2@test.local")
    client.post("/auth/forgot-password", json={"email": "u2@test.local", "new_password": "newpassword1"})

    resp = client.post("/auth/login", json={"email": "u2@test.local", "password": "oldpassword1"})
    assert resp.status_code == 200


def test_new_password_active_after_admin_approves_reset(client):
    client.post("/auth/register", json={"email": "u3@test.local", "password": "oldpassword1"})
    approve_by_email(client, "u3@test.local")
    client.post("/auth/forgot-password", json={"email": "u3@test.local", "new_password": "newpassword1"})

    client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    resets = client.get("/admin/password-resets").json()
    reset_id = next(r["id"] for r in resets if r["user_email"] == "u3@test.local")
    approve_resp = client.post(f"/admin/password-resets/{reset_id}/approve")
    assert approve_resp.status_code == 200

    resp_old = client.post("/auth/login", json={"email": "u3@test.local", "password": "oldpassword1"})
    assert resp_old.status_code == 401

    resp_new = client.post("/auth/login", json={"email": "u3@test.local", "password": "newpassword1"})
    assert resp_new.status_code == 200


def test_reject_password_reset_keeps_old_password(client):
    client.post("/auth/register", json={"email": "u5@test.local", "password": "oldpassword1"})
    approve_by_email(client, "u5@test.local")
    client.post("/auth/forgot-password", json={"email": "u5@test.local", "new_password": "newpassword1"})

    client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    resets = client.get("/admin/password-resets").json()
    reset_id = next(r["id"] for r in resets if r["user_email"] == "u5@test.local")
    client.post(f"/admin/password-resets/{reset_id}/reject")

    resp_old = client.post("/auth/login", json={"email": "u5@test.local", "password": "oldpassword1"})
    assert resp_old.status_code == 200
