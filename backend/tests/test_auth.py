def test_login_returns_token_and_user(client, seed):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.tn", "password": "Admin123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "admin@demo.tn"
    assert body["user"]["role"] == "admin"


def test_wrong_password_is_rejected(client, seed):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.tn", "password": "nope"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_requires_a_token(client, seed):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_the_current_user(client, seed):
    response = client.get("/api/v1/auth/me", headers=seed["operator_headers"])
    assert response.status_code == 200
    assert response.json()["role"] == "operator"


def test_admin_ping_enforces_role(client, seed):
    assert client.get("/api/v1/admin/ping", headers=seed["admin_headers"]).status_code == 200
    assert client.get("/api/v1/admin/ping", headers=seed["operator_headers"]).status_code == 403
    assert client.get("/api/v1/admin/ping").status_code == 401
