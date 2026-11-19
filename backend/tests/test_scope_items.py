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


def create_project_helper(client, agency_headers, project_name="Website Build"):
    """Helper to create a client and project."""
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
    return pr_resp.json()


def test_create_scope_item_success(client):
    agency = create_test_agency(client, "Scope Studio", "scope@studio.io", "Password123!")
    proj = create_project_helper(client, agency["headers"], "E-commerce Redesign")

    payload = {
        "project_id": proj["id"],
        "included_description": "Home page design, five product pages, contact form.",
        "not_included_description": "Hindi language version, payment gateway integration.",
    }
    resp = client.post("/api/v1/scope-items", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()

    assert data["project_id"] == proj["id"]
    assert data["workspace_id"] == agency["workspace_id"]
    assert data["included_description"] == "Home page design, five product pages, contact form."
    assert data["not_included_description"] == "Hindi language version, payment gateway integration."
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_scope_item_validation_error(client):
    agency = create_test_agency(client, "Valid Studio", "val@studio.io", "Password123!")
    proj = create_project_helper(client, agency["headers"])

    # Missing not_included_description
    resp = client.post(
        "/api/v1/scope-items",
        json={"project_id": proj["id"], "included_description": "Only included"},
        headers=agency["headers"],
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Empty string for included_description
    resp2 = client.post(
        "/api/v1/scope-items",
        json={
            "project_id": proj["id"],
            "included_description": "",
            "not_included_description": "Something not included",
        },
        headers=agency["headers"],
    )
    assert resp2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_scope_item_nonexistent_project(client):
    agency = create_test_agency(client, "Ghost Studio", "ghost@studio.io", "Password123!")
    random_project_id = str(uuid.uuid4())

    payload = {
        "project_id": random_project_id,
        "included_description": "Included deliverables",
        "not_included_description": "Excluded deliverables",
    }
    resp = client.post("/api/v1/scope-items", json=payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found in your workspace" in resp.json()["detail"].lower()


def test_create_scope_item_cross_workspace_project_rejected(client):
    agency_a = create_test_agency(client, "Agency A Scope", "a_scope@test.com", "Password123!")
    agency_b = create_test_agency(client, "Agency B Scope", "b_scope@test.com", "Password123!")

    # Agency A creates project A
    proj_a = create_project_helper(client, agency_a["headers"], "Project A")

    # Agency B attempts to create a scope item linked to Agency A's project!
    cross_payload = {
        "project_id": proj_a["id"],
        "included_description": "Malicious inclusion",
        "not_included_description": "Malicious exclusion",
    }
    resp = client.post("/api/v1/scope-items", json=cross_payload, headers=agency_b["headers"])
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "not found in your workspace" in resp.json()["detail"].lower()


def test_list_and_filter_scope_items(client):
    agency = create_test_agency(client, "Filter Studio", "filter@studio.io", "Password123!")
    proj_1 = create_project_helper(client, agency["headers"], "Project One")
    proj_2 = create_project_helper(client, agency["headers"], "Project Two")

    # Create 2 items for proj_1 and 1 item for proj_2
    client.post(
        "/api/v1/scope-items",
        json={"project_id": proj_1["id"], "included_description": "P1 Item 1", "not_included_description": "None"},
        headers=agency["headers"],
    )
    client.post(
        "/api/v1/scope-items",
        json={"project_id": proj_1["id"], "included_description": "P1 Item 2", "not_included_description": "None"},
        headers=agency["headers"],
    )
    client.post(
        "/api/v1/scope-items",
        json={"project_id": proj_2["id"], "included_description": "P2 Item 1", "not_included_description": "None"},
        headers=agency["headers"],
    )

    # List all in workspace
    all_resp = client.get("/api/v1/scope-items", headers=agency["headers"])
    assert all_resp.status_code == status.HTTP_200_OK
    assert len(all_resp.json()) == 3

    # Filter by proj_1
    p1_resp = client.get(f"/api/v1/scope-items?project_id={proj_1['id']}", headers=agency["headers"])
    assert p1_resp.status_code == status.HTTP_200_OK
    assert len(p1_resp.json()) == 2
    for item in p1_resp.json():
        assert item["project_id"] == proj_1["id"]

    # Filter by proj_2
    p2_resp = client.get(f"/api/v1/scope-items?project_id={proj_2['id']}", headers=agency["headers"])
    assert p2_resp.status_code == status.HTTP_200_OK
    assert len(p2_resp.json()) == 1
    assert p2_resp.json()[0]["project_id"] == proj_2["id"]


def test_get_scope_item_by_id(client):
    agency = create_test_agency(client, "Get Studio", "get@studio.io", "Password123!")
    proj = create_project_helper(client, agency["headers"])

    created = client.post(
        "/api/v1/scope-items",
        json={
            "project_id": proj["id"],
            "included_description": "Single scope item",
            "not_included_description": "Not included",
        },
        headers=agency["headers"],
    ).json()

    resp = client.get(f"/api/v1/scope-items/{created['id']}", headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["id"] == created["id"]
    assert resp.json()["included_description"] == "Single scope item"


def test_update_scope_item(client):
    agency = create_test_agency(client, "Upd Studio", "upd@studio.io", "Password123!")
    proj = create_project_helper(client, agency["headers"])

    created = client.post(
        "/api/v1/scope-items",
        json={
            "project_id": proj["id"],
            "included_description": "Old included",
            "not_included_description": "Old excluded",
        },
        headers=agency["headers"],
    ).json()

    update_payload = {
        "included_description": "Updated included deliverables",
        "not_included_description": "Updated excluded deliverables",
    }
    resp = client.put(f"/api/v1/scope-items/{created['id']}", json=update_payload, headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["included_description"] == "Updated included deliverables"
    assert resp.json()["not_included_description"] == "Updated excluded deliverables"


def test_update_scope_item_cross_workspace_project_rejected(client):
    agency_a = create_test_agency(client, "Agency A Upd", "a_upd@test.com", "Password123!")
    agency_b = create_test_agency(client, "Agency B Upd", "b_upd@test.com", "Password123!")

    proj_a = create_project_helper(client, agency_a["headers"], "Project A")
    proj_b = create_project_helper(client, agency_b["headers"], "Project B")

    item_a = client.post(
        "/api/v1/scope-items",
        json={"project_id": proj_a["id"], "included_description": "A", "not_included_description": "None"},
        headers=agency_a["headers"],
    ).json()

    # Agency A attempts to move item_a to Agency B's project!
    bad_update = {"project_id": proj_b["id"]}
    resp = client.put(f"/api/v1/scope-items/{item_a['id']}", json=bad_update, headers=agency_a["headers"])
    assert resp.status_code == status.HTTP_404_NOT_FOUND
    assert "target project not found in your workspace" in resp.json()["detail"].lower()


def test_delete_scope_item(client):
    agency = create_test_agency(client, "Del Studio", "del@studio.io", "Password123!")
    proj = create_project_helper(client, agency["headers"])

    created = client.post(
        "/api/v1/scope-items",
        json={
            "project_id": proj["id"],
            "included_description": "Delete me",
            "not_included_description": "None",
        },
        headers=agency["headers"],
    ).json()

    del_resp = client.delete(f"/api/v1/scope-items/{created['id']}", headers=agency["headers"])
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify subsequent GET returns 404
    get_resp = client.get(f"/api/v1/scope-items/{created['id']}", headers=agency["headers"])
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_unauthenticated_scope_item_access(client):
    resp = client.get("/api/v1/scope-items")
    assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_scope_item_cross_workspace_isolation(client):
    agency_a = create_test_agency(client, "Agency A Iso Scope", "a_iso_s@test.com", "Password123!")
    agency_b = create_test_agency(client, "Agency B Iso Scope", "b_iso_s@test.com", "Password123!")

    proj_a = create_project_helper(client, agency_a["headers"], "Project A")
    proj_b = create_project_helper(client, agency_b["headers"], "Project B")

    item_a = client.post(
        "/api/v1/scope-items",
        json={
            "project_id": proj_a["id"],
            "included_description": "Agency A Included",
            "not_included_description": "Agency A Excluded",
        },
        headers=agency_a["headers"],
    ).json()

    item_b = client.post(
        "/api/v1/scope-items",
        json={
            "project_id": proj_b["id"],
            "included_description": "Agency B Included",
            "not_included_description": "Agency B Excluded",
        },
        headers=agency_b["headers"],
    ).json()

    # Agency A list must only include item_a
    list_a = client.get("/api/v1/scope-items", headers=agency_a["headers"]).json()
    ids_a = [item["id"] for item in list_a]
    assert item_a["id"] in ids_a
    assert item_b["id"] not in ids_a

    # Agency A attempting to GET item_b returns 404
    resp_get = client.get(f"/api/v1/scope-items/{item_b['id']}", headers=agency_a["headers"])
    assert resp_get.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to PUT item_b returns 404
    resp_put = client.put(
        f"/api/v1/scope-items/{item_b['id']}",
        json={"included_description": "Tampered"},
        headers=agency_a["headers"],
    )
    assert resp_put.status_code == status.HTTP_404_NOT_FOUND

    # Agency A attempting to DELETE item_b returns 404
    resp_del = client.delete(f"/api/v1/scope-items/{item_b['id']}", headers=agency_a["headers"])
    assert resp_del.status_code == status.HTTP_404_NOT_FOUND

    # Verify Agency B item is untouched
    verify_b = client.get(f"/api/v1/scope-items/{item_b['id']}", headers=agency_b["headers"])
    assert verify_b.status_code == status.HTTP_200_OK
    assert verify_b.json()["included_description"] == "Agency B Included"
