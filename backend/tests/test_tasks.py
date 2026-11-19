import uuid
from datetime import date
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


def create_project_and_scope_item(client, agency_headers, project_name="Web App", item_included="Core API"):
    """Helper to create client, project, and scope item."""
    cl_resp = client.post(
        "/api/v1/clients",
        json={"name": f"Client for {project_name}", "email": "client@example.com"},
        headers=agency_headers,
    )
    client_id = cl_resp.json()["id"]

    pr_resp = client.post(
        "/api/v1/projects",
        json={"client_id": client_id, "name": project_name, "status": "Active"},
        headers=agency_headers,
    )
    project_id = pr_resp.json()["id"]

    sc_resp = client.post(
        "/api/v1/scope-items",
        json={
            "project_id": project_id,
            "included_description": item_included,
            "not_included_description": "Exclusions",
        },
        headers=agency_headers,
    )
    scope_item_id = sc_resp.json()["id"]

    return {
        "project_id": project_id,
        "scope_item_id": scope_item_id,
        "project_name": project_name,
        "scope_item_included": item_included,
    }


def test_create_task_success(client):
    agency = create_test_agency(client, "Task Agency", "task@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"], "E-commerce Shop", "Cart Checkout Flow")

    payload = {
        "project_id": setup["project_id"],
        "scope_item_id": setup["scope_item_id"],
        "title": "Build Stripe Checkout Integration",
        "due_date": "2026-12-15",
        "status": "To do",
    }
    resp = client.post("/api/v1/tasks", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    assert data["title"] == "Build Stripe Checkout Integration"
    assert data["status"] == "To do"
    assert data["due_date"] == "2026-12-15"
    assert data["project_id"] == setup["project_id"]
    assert data["scope_item_id"] == setup["scope_item_id"]
    assert data["workspace_id"] == agency["workspace_id"]
    assert data["project_name"] == "E-commerce Shop"
    assert "Cart Checkout Flow" in data["scope_item_summary"]
    assert "id" in data


def test_create_task_default_status(client):
    agency = create_test_agency(client, "Def Status Agency", "def@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"])

    payload = {
        "project_id": setup["project_id"],
        "scope_item_id": setup["scope_item_id"],
        "title": "Implement Unit Tests",
    }
    resp = client.post("/api/v1/tasks", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["status"] == "To do"


def test_create_task_invalid_status_rejected(client):
    agency = create_test_agency(client, "Status Agency", "status@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"])

    payload = {
        "project_id": setup["project_id"],
        "scope_item_id": setup["scope_item_id"],
        "title": "Invalid Status Task",
        "status": "Reviewing",  # Only To do, Doing, Done allowed
    }
    resp = client.post("/api/v1/tasks", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_task_invalid_project_reference(client):
    agency = create_test_agency(client, "NoProj Agency", "noproj@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"])
    random_project_id = str(uuid.uuid4())

    payload = {
        "project_id": random_project_id,
        "scope_item_id": setup["scope_item_id"],
        "title": "Orphan Project Task",
    }
    resp = client.post("/api/v1/tasks", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "project not found in your workspace" in resp.json()["detail"].lower()


def test_create_task_invalid_scope_item_reference(client):
    agency = create_test_agency(client, "NoScope Agency", "noscope@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"])
    random_scope_id = str(uuid.uuid4())

    payload = {
        "project_id": setup["project_id"],
        "scope_item_id": random_scope_id,
        "title": "Orphan Scope Task",
    }
    resp = client.post("/api/v1/tasks", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "scope item not found in your workspace" in resp.json()["detail"].lower()


def test_create_task_scope_item_from_different_project_rejected(client):
    agency = create_test_agency(client, "Mismatch Agency", "mismatch@agency.io", "Password123!")
    
    # Project 1 with Scope Item 1
    p1 = create_project_and_scope_item(client, agency["headers"], "Project 1", "Scope 1")
    # Project 2 with Scope Item 2
    p2 = create_project_and_scope_item(client, agency["headers"], "Project 2", "Scope 2")

    # Attempt to pair Project 1 with Scope Item 2
    payload = {
        "project_id": p1["project_id"],
        "scope_item_id": p2["scope_item_id"],
        "title": "Mismatched Task",
    }
    resp = client.post("/api/v1/tasks", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "does not belong to the specified project" in resp.json()["detail"].lower()


def test_list_and_filter_tasks(client):
    agency = create_test_agency(client, "Filter Task Agency", "filter_t@agency.io", "Password123!")
    p1 = create_project_and_scope_item(client, agency["headers"], "P1", "S1")
    p2 = create_project_and_scope_item(client, agency["headers"], "P2", "S2")

    # Task 1 in P1 (To do)
    t1 = client.post(
        "/api/v1/tasks",
        json={"project_id": p1["project_id"], "scope_item_id": p1["scope_item_id"], "title": "T1", "status": "To do"},
        headers=agency["headers"],
    ).json()

    # Task 2 in P1 (Done)
    t2 = client.post(
        "/api/v1/tasks",
        json={"project_id": p1["project_id"], "scope_item_id": p1["scope_item_id"], "title": "T2", "status": "Done"},
        headers=agency["headers"],
    ).json()

    # Task 3 in P2 (Doing)
    t3 = client.post(
        "/api/v1/tasks",
        json={"project_id": p2["project_id"], "scope_item_id": p2["scope_item_id"], "title": "T3", "status": "Doing"},
        headers=agency["headers"],
    ).json()

    # List all in workspace
    all_resp = client.get("/api/v1/tasks", headers=agency["headers"])
    assert all_resp.status_code == status.HTTP_200_OK
    assert len(all_resp.json()) == 3

    # Filter by project_id
    p1_resp = client.get(f"/api/v1/tasks?project_id={p1['project_id']}", headers=agency["headers"])
    assert p1_resp.status_code == status.HTTP_200_OK
    assert len(p1_resp.json()) == 2

    # Filter by status = Done
    done_resp = client.get("/api/v1/tasks?status=Done", headers=agency["headers"])
    assert done_resp.status_code == status.HTTP_200_OK
    assert len(done_resp.json()) == 1
    assert done_resp.json()[0]["id"] == t2["id"]


def test_get_task_by_id(client):
    agency = create_test_agency(client, "Get Task Agency", "get_t@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"])

    created = client.post(
        "/api/v1/tasks",
        json={"project_id": setup["project_id"], "scope_item_id": setup["scope_item_id"], "title": "Get Target"},
        headers=agency["headers"],
    ).json()

    resp = client.get(f"/api/v1/tasks/{created['id']}", headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == created["id"]
    assert resp.json()["title"] == "Get Target"


def test_update_task_fields_and_status(client):
    agency = create_test_agency(client, "Upd Task Agency", "upd_t@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"])

    created = client.post(
        "/api/v1/tasks",
        json={"project_id": setup["project_id"], "scope_item_id": setup["scope_item_id"], "title": "Initial Task", "status": "To do"},
        headers=agency["headers"],
    ).json()

    # Update title and status
    update_payload = {
        "title": "Completed Task",
        "status": "Done",
        "due_date": "2026-11-30",
    }
    resp = client.put(f"/api/v1/tasks/{created['id']}", json=update_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["title"] == "Completed Task"
    assert data["status"] == "Done"
    assert data["due_date"] == "2026-11-30"


def test_delete_task(client):
    agency = create_test_agency(client, "Del Task Agency", "del_t@agency.io", "Password123!")
    setup = create_project_and_scope_item(client, agency["headers"])

    created = client.post(
        "/api/v1/tasks",
        json={"project_id": setup["project_id"], "scope_item_id": setup["scope_item_id"], "title": "Delete Me Task"},
        headers=agency["headers"],
    ).json()

    del_resp = client.delete(f"/api/v1/tasks/{created['id']}", headers=agency["headers"])
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Subsequent GET returns 404
    get_resp = client.get(f"/api/v1/tasks/{created['id']}", headers=agency["headers"])
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_unauthenticated_task_access(client):
    resp = client.get("/api/v1/tasks")
    assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_task_cross_workspace_isolation(client):
    agency_a = create_test_agency(client, "Agency A Tasks", "a_t@test.com", "Password123!")
    agency_b = create_test_agency(client, "Agency B Tasks", "b_t@test.com", "Password123!")

    setup_a = create_project_and_scope_item(client, agency_a["headers"], "PA", "SA")
    setup_b = create_project_and_scope_item(client, agency_b["headers"], "PB", "SB")

    task_a = client.post(
        "/api/v1/tasks",
        json={"project_id": setup_a["project_id"], "scope_item_id": setup_a["scope_item_id"], "title": "Task A"},
        headers=agency_a["headers"],
    ).json()

    task_b = client.post(
        "/api/v1/tasks",
        json={"project_id": setup_b["project_id"], "scope_item_id": setup_b["scope_item_id"], "title": "Task B"},
        headers=agency_b["headers"],
    ).json()

    # Agency A list must only include Task A
    list_a = client.get("/api/v1/tasks", headers=agency_a["headers"]).json()
    ids_a = [t["id"] for t in list_a]
    assert task_a["id"] in ids_a
    assert task_b["id"] not in ids_a

    # Agency A attempting to GET Task B directly returns 404
    resp_get = client.get(f"/api/v1/tasks/{task_b['id']}", headers=agency_a["headers"])
    assert resp_get.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to PUT Task B directly returns 404
    resp_put = client.put(
        f"/api/v1/tasks/{task_b['id']}",
        json={"title": "Hacked Title"},
        headers=agency_a["headers"],
    )
    assert resp_put.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to DELETE Task B directly returns 404
    resp_del = client.delete(f"/api/v1/tasks/{task_b['id']}", headers=agency_a["headers"])
    assert resp_del.status_code == status.HTTP_404_NOT_FOUND

    # Verify Agency B task is untouched
    verify_b = client.get(f"/api/v1/tasks/{task_b['id']}", headers=agency_b["headers"])
    assert verify_b.status_code == status.HTTP_200_OK
    assert verify_b.json()["title"] == "Task B"
