from fastapi import status


def create_test_agency(client, agency_name, email, password):
    """Helper to sign up an agency and return its auth token and user/workspace metadata."""
    payload = {
        "agency_name": agency_name,
        "email": email,
        "password": password,
        "full_name": f"{agency_name} Admin",
    }
    resp = client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    return {
        "token": data["access_token"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "workspace_id": data["workspace"]["id"],
        "user_id": data["user"]["id"],
    }


def test_create_client_success(client):
    agency = create_test_agency(client, "Nexus Agency", "admin@nexus.io", "NexusPass123!")
    
    payload = {
        "name": "Acme Global",
        "email": "contact@acmeglobal.com",
    }
    resp = client.post("/api/v1/clients", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["name"] == "Acme Global"
    assert data["email"] == "contact@acmeglobal.com"
    assert data["workspace_id"] == agency["workspace_id"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_client_validation_error(client):
    agency = create_test_agency(client, "Val Agency", "val@agency.io", "NexusPass123!")
    
    # Missing name
    resp = client.post("/api/v1/clients", json={"email": "bad@email.com"}, headers=agency["headers"])
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Invalid email format
    resp2 = client.post(
        "/api/v1/clients",
        json={"name": "Valid Name", "email": "not-an-email"},
        headers=agency["headers"],
    )
    assert resp2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_clients(client):
    agency = create_test_agency(client, "Listing Agency", "listing@agency.io", "ListingPass123!")
    
    # Create two clients
    client.post("/api/v1/clients", json={"name": "Client 1", "email": "c1@test.com"}, headers=agency["headers"])
    client.post("/api/v1/clients", json={"name": "Client 2", "email": "c2@test.com"}, headers=agency["headers"])

    resp = client.get("/api/v1/clients", headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert len(data) == 2
    names = [c["name"] for c in data]
    assert "Client 1" in names
    assert "Client 2" in names


def test_get_client_by_id(client):
    agency = create_test_agency(client, "Single Agency", "single@agency.io", "SinglePass123!")
    created = client.post(
        "/api/v1/clients",
        json={"name": "Unique Client", "email": "unique@test.com"},
        headers=agency["headers"],
    ).json()

    resp = client.get(f"/api/v1/clients/{created['id']}", headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == created["id"]
    assert resp.json()["name"] == "Unique Client"


def test_update_client(client):
    agency = create_test_agency(client, "Update Agency", "update@agency.io", "UpdatePass123!")
    created = client.post(
        "/api/v1/clients",
        json={"name": "Old Client Name", "email": "old@test.com"},
        headers=agency["headers"],
    ).json()

    update_payload = {"name": "New Client Name", "email": "new@test.com"}
    resp = client.put(f"/api/v1/clients/{created['id']}", json=update_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["name"] == "New Client Name"
    assert resp.json()["email"] == "new@test.com"


def test_delete_client(client):
    agency = create_test_agency(client, "Delete Agency", "delete@agency.io", "DeletePass123!")
    created = client.post(
        "/api/v1/clients",
        json={"name": "To Delete", "email": "delete@test.com"},
        headers=agency["headers"],
    ).json()

    del_resp = client.delete(f"/api/v1/clients/{created['id']}", headers=agency["headers"])
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify subsequent GET returns 404
    get_resp = client.get(f"/api/v1/clients/{created['id']}", headers=agency["headers"])
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_unauthenticated_client_access(client):
    resp = client.get("/api/v1/clients")
    assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_client_cross_workspace_isolation(client):
    agency_a = create_test_agency(client, "Agency A", "a@test.com", "PasswordA123!")
    agency_b = create_test_agency(client, "Agency B", "b@test.com", "PasswordB123!")

    # Agency A creates a client
    client_a = client.post(
        "/api/v1/clients",
        json={"name": "Client A", "email": "client_a@test.com"},
        headers=agency_a["headers"],
    ).json()

    # Agency B creates a client
    client_b = client.post(
        "/api/v1/clients",
        json={"name": "Client B", "email": "client_b@test.com"},
        headers=agency_b["headers"],
    ).json()

    # Agency A cannot see Client B in their list
    list_a = client.get("/api/v1/clients", headers=agency_a["headers"]).json()
    ids_a = [c["id"] for c in list_a]
    assert client_a["id"] in ids_a
    assert client_b["id"] not in ids_a

    # Agency A attempting to GET Client B directly by ID must fail with 404
    resp_get = client.get(f"/api/v1/clients/{client_b['id']}", headers=agency_a["headers"])
    assert resp_get.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to PUT Client B directly by ID must fail with 404
    resp_put = client.put(
        f"/api/v1/clients/{client_b['id']}",
        json={"name": "Hacked Name"},
        headers=agency_a["headers"],
    )
    assert resp_put.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to DELETE Client B directly by ID must fail with 404
    resp_del = client.delete(f"/api/v1/clients/{client_b['id']}", headers=agency_a["headers"])
    assert resp_del.status_code == status.HTTP_404_NOT_FOUND

    # Verify Client B is still alive and intact for Agency B
    verify_b = client.get(f"/api/v1/clients/{client_b['id']}", headers=agency_b["headers"])
    assert verify_b.status_code == status.HTTP_200_OK
    assert verify_b.json()["name"] == "Client B"
