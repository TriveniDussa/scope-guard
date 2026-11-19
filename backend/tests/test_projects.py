import uuid
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


def test_create_project_success(client):
    agency = create_test_agency(client, "Alpha Design", "admin@alphadesign.com", "Password123!")
    
    # 1. Create client first
    cl_resp = client.post(
        "/api/v1/clients",
        json={"name": "Nike Global", "email": "nike@nike.com"},
        headers=agency["headers"],
    )
    client_id = cl_resp.json()["id"]

    # 2. Create project
    proj_payload = {
        "client_id": client_id,
        "name": "Summer Campaign Landing Page",
        "status": "Active",
    }
    resp = client.post("/api/v1/projects", json=proj_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["name"] == "Summer Campaign Landing Page"
    assert data["status"] == "Active"
    assert data["client_id"] == client_id
    assert data["workspace_id"] == agency["workspace_id"]
    assert "id" in data


def test_create_project_default_status(client):
    agency = create_test_agency(client, "Beta Tech", "beta@tech.com", "Password123!")
    cl_resp = client.post(
        "/api/v1/clients",
        json={"name": "Adidas Corp", "email": "corp@adidas.com"},
        headers=agency["headers"],
    )
    client_id = cl_resp.json()["id"]

    # Status omitted, should default to Active
    proj_payload = {
        "client_id": client_id,
        "name": "Mobile App Refresh",
    }
    resp = client.post("/api/v1/projects", json=proj_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["status"] == "Active"


def test_create_project_done_status(client):
    agency = create_test_agency(client, "Gamma Agency", "gamma@agency.com", "Password123!")
    cl_resp = client.post(
        "/api/v1/clients",
        json={"name": "Client Gamma", "email": "g@gamma.com"},
        headers=agency["headers"],
    )
    client_id = cl_resp.json()["id"]

    proj_payload = {
        "client_id": client_id,
        "name": "Completed Redesign",
        "status": "Done",
    }
    resp = client.post("/api/v1/projects", json=proj_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["status"] == "Done"


def test_create_project_invalid_status_rejected(client):
    agency = create_test_agency(client, "Delta Studio", "delta@studio.com", "Password123!")
    cl_resp = client.post(
        "/api/v1/clients",
        json={"name": "Puma Inc", "email": "puma@puma.com"},
        headers=agency["headers"],
    )
    client_id = cl_resp.json()["id"]

    # Status not in [Active, Done]
    proj_payload = {
        "client_id": client_id,
        "name": "Invalid Project",
        "status": "In Progress",  # Only Active or Done allowed
    }
    resp = client.post("/api/v1/projects", json=proj_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_project_nonexistent_client_rejected(client):
    agency = create_test_agency(client, "Epsilon Agency", "eps@agency.com", "Password123!")
    random_client_id = str(uuid.uuid4())

    proj_payload = {
        "client_id": random_client_id,
        "name": "Orphan Project",
    }
    resp = client.post("/api/v1/projects", json=proj_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in resp.json()["detail"].lower()


def test_create_project_cross_workspace_client_rejected(client):
    agency_a = create_test_agency(client, "Agency A Proj", "agency_a_p@test.com", "Password123!")
    agency_b = create_test_agency(client, "Agency B Proj", "agency_b_p@test.com", "Password123!")

    # Agency A creates client A
    client_a = client.post(
        "/api/v1/clients",
        json={"name": "Client A", "email": "a@client.com"},
        headers=agency_a["headers"],
    ).json()

    # Agency B tries to create a project attached to Agency A's client!
    cross_proj_payload = {
        "client_id": client_a["id"],
        "name": "Illegal Cross-Workspace Project",
    }
    resp = client.post("/api/v1/projects", json=cross_proj_payload, headers=agency_b["headers"])
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found in your workspace" in resp.json()["detail"].lower()


def test_list_and_filter_projects(client):
    agency = create_test_agency(client, "Zeta Creative", "zeta@creative.com", "Password123!")
    cl = client.post(
        "/api/v1/clients",
        json={"name": "Client Zeta", "email": "zeta@client.com"},
        headers=agency["headers"],
    ).json()

    # Create one Active and one Done project
    p1 = client.post(
        "/api/v1/projects",
        json={"client_id": cl["id"], "name": "Active P1", "status": "Active"},
        headers=agency["headers"],
    ).json()
    p2 = client.post(
        "/api/v1/projects",
        json={"client_id": cl["id"], "name": "Done P2", "status": "Done"},
        headers=agency["headers"],
    ).json()

    # List all
    all_resp = client.get("/api/v1/projects", headers=agency["headers"])
    assert all_resp.status_code == status.HTTP_200_OK
    assert len(all_resp.json()) == 2

    # Filter Active
    active_resp = client.get("/api/v1/projects?status=Active", headers=agency["headers"])
    assert active_resp.status_code == status.HTTP_200_OK
    assert len(active_resp.json()) == 1
    assert active_resp.json()[0]["id"] == p1["id"]

    # Filter Done
    done_resp = client.get("/api/v1/projects?status=Done", headers=agency["headers"])
    assert done_resp.status_code == status.HTTP_200_OK
    assert len(done_resp.json()) == 1
    assert done_resp.json()[0]["id"] == p2["id"]


def test_update_project_and_status_transition(client):
    agency = create_test_agency(client, "Theta Studio", "theta@studio.com", "Password123!")
    cl = client.post(
        "/api/v1/clients",
        json={"name": "Client Theta", "email": "theta@client.com"},
        headers=agency["headers"],
    ).json()

    proj = client.post(
        "/api/v1/projects",
        json={"client_id": cl["id"], "name": "Initial Name", "status": "Active"},
        headers=agency["headers"],
    ).json()

    # Transition to Done and change name
    update_payload = {"name": "Finished Project", "status": "Done"}
    resp = client.put(f"/api/v1/projects/{proj['id']}", json=update_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["name"] == "Finished Project"
    assert data["status"] == "Done"


def test_delete_project(client):
    agency = create_test_agency(client, "Iota Studio", "iota@studio.com", "Password123!")
    cl = client.post(
        "/api/v1/clients",
        json={"name": "Client Iota", "email": "iota@client.com"},
        headers=agency["headers"],
    ).json()

    proj = client.post(
        "/api/v1/projects",
        json={"client_id": cl["id"], "name": "To Delete"},
        headers=agency["headers"],
    ).json()

    del_resp = client.delete(f"/api/v1/projects/{proj['id']}", headers=agency["headers"])
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify 404 on subsequent get
    get_resp = client.get(f"/api/v1/projects/{proj['id']}", headers=agency["headers"])
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_project_cross_workspace_isolation(client):
    agency_a = create_test_agency(client, "Agency A Iso", "a_iso@test.com", "PasswordA123!")
    agency_b = create_test_agency(client, "Agency B Iso", "b_iso@test.com", "PasswordB123!")

    # Agency A client & project
    cl_a = client.post(
        "/api/v1/clients",
        json={"name": "Client A", "email": "a@test.com"},
        headers=agency_a["headers"],
    ).json()
    p_a = client.post(
        "/api/v1/projects",
        json={"client_id": cl_a["id"], "name": "Project Alpha", "status": "Active"},
        headers=agency_a["headers"],
    ).json()

    # Agency B client & project
    cl_b = client.post(
        "/api/v1/clients",
        json={"name": "Client B", "email": "b@test.com"},
        headers=agency_b["headers"],
    ).json()
    p_b = client.post(
        "/api/v1/projects",
        json={"client_id": cl_b["id"], "name": "Project Beta", "status": "Active"},
        headers=agency_b["headers"],
    ).json()

    # Agency A cannot see Project B in list
    list_a = client.get("/api/v1/projects", headers=agency_a["headers"]).json()
    ids_a = [p["id"] for p in list_a]
    assert p_a["id"] in ids_a
    assert p_b["id"] not in ids_a

    # Agency A attempting to GET Project B directly by ID returns 404
    resp_get = client.get(f"/api/v1/projects/{p_b['id']}", headers=agency_a["headers"])
    assert resp_get.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to PUT Project B directly by ID returns 404
    resp_put = client.put(
        f"/api/v1/projects/{p_b['id']}",
        json={"name": "Tampered Name"},
        headers=agency_a["headers"],
    )
    assert resp_put.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to DELETE Project B directly by ID returns 404
    resp_del = client.delete(f"/api/v1/projects/{p_b['id']}", headers=agency_a["headers"])
    assert resp_del.status_code == status.HTTP_404_NOT_FOUND

    # Verify Project B is untouched for Agency B
    verify_b = client.get(f"/api/v1/projects/{p_b['id']}", headers=agency_b["headers"])
    assert verify_b.status_code == status.HTTP_200_OK
    assert verify_b.json()["name"] == "Project Beta"
