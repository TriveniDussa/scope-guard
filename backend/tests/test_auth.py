from fastapi import status


def test_agency_signup_success(client):
    payload = {
        "agency_name": "Apex Creative Studio",
        "email": "owner@apexstudio.io",
        "password": "SuperSecretPassword123!",
        "full_name": "Marcus Vance",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "owner@apexstudio.io"
    assert data["user"]["full_name"] == "Marcus Vance"
    assert data["user"]["role"] == "agency_admin"
    assert data["workspace"]["name"] == "Apex Creative Studio"
    assert data["workspace"]["slug"] == "apex-creative-studio"

    # Security Check: Ensure hashed_password is never leaked
    assert "hashed_password" not in data["user"]
    assert "password" not in data["user"]


def test_agency_signup_duplicate_email(client):
    payload = {
        "agency_name": "First Agency",
        "email": "duplicate@agency.io",
        "password": "Password123!",
        "full_name": "Alice Admin",
    }
    resp1 = client.post("/api/v1/auth/signup", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED

    payload2 = {
        "agency_name": "Second Agency",
        "email": "duplicate@agency.io",
        "password": "DifferentPassword123!",
        "full_name": "Bob Admin",
    }
    resp2 = client.post("/api/v1/auth/signup", json=payload2)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in resp2.json()["detail"].lower()


def test_login_success(client):
    # Setup account
    signup_payload = {
        "agency_name": "Velocity Labs",
        "email": "sarah@velocitylabs.com",
        "password": "CorrectPassword123!",
        "full_name": "Sarah Connor",
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    # Login
    login_payload = {
        "email": "sarah@velocitylabs.com",
        "password": "CorrectPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    signup_payload = {
        "agency_name": "Delta Agency",
        "email": "alex@delta.com",
        "password": "CorrectPassword123!",
        "full_name": "Alex Mercer",
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    # Wrong password
    login_payload = {
        "email": "alex@delta.com",
        "password": "WRONG_PASSWORD_XYZ",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_nonexistent_email(client):
    login_payload = {
        "email": "ghost@doesnotexist.com",
        "password": "AnyPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_me_endpoint_with_valid_token(client):
    signup_payload = {
        "agency_name": "Quantum Digital",
        "email": "elena@quantum.io",
        "password": "ElenaSecure123!",
        "full_name": "Elena Rostova",
    }
    signup_resp = client.post("/api/v1/auth/signup", json=signup_payload)
    token = signup_resp.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user"]["email"] == "elena@quantum.io"
    assert data["workspace"]["name"] == "Quantum Digital"
    assert "hashed_password" not in data["user"]


def test_protected_me_endpoint_without_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_protected_me_endpoint_with_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer bogus_invalid_token_12345"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
