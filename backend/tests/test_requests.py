import uuid
import pytest
from fastapi import status

from app.main import app
from app.models.request import Request
from app.services.ai.base import (
    AIClassificationResult,
    AIServiceError,
    BaseAIService,
    ClassificationEnum,
)
from app.services.ai.factory import get_ai_service


class MockAIService(BaseAIService):
    def __init__(
        self,
        classification: str = "In scope",
        reason: str = "Matches agreed scope item.",
        client_reply: str = "We'll proceed with this task as requested.",
        should_raise: bool = False,
    ):
        self.classification = classification
        self.reason = reason
        self.client_reply = client_reply
        self.should_raise = should_raise
        self.last_client_request = None
        self.last_scope_items = None

    def classify_request(
        self,
        client_request: str,
        scope_items: list,
        lessons: list = None,
    ) -> AIClassificationResult:
        if self.should_raise:
            raise AIServiceError("Simulated provider quota limit exceeded")
        self.last_client_request = client_request
        self.last_scope_items = scope_items
        self.last_lessons = lessons
        return AIClassificationResult(
            classification=ClassificationEnum(self.classification),
            reason=self.reason,
            client_reply=self.client_reply,
        )


def create_agency(client, agency_name, email, password="Password123!"):
    resp = client.post(
        "/api/v1/auth/signup",
        json={
            "agency_name": agency_name,
            "email": email,
            "password": password,
            "full_name": f"{agency_name} Admin",
        },
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    return {
        "token": data["access_token"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "workspace_id": data["workspace"]["id"],
        "user_id": data["user"]["id"],
    }


def create_project_with_scope(client, agency_headers, project_name="Website Redesign"):
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
            "included_description": "Homepage design, responsive layout, contact form",
            "not_included_description": "SEO copywriting, Hindi translations, custom CRM integrations",
        },
        headers=agency_headers,
    )
    scope_item_id = sc_resp.json()["id"]

    return {
        "project_id": project_id,
        "scope_item_id": scope_item_id,
        "client_id": client_id,
    }


# Test 1: Successful "In scope" classification
def test_check_request_in_scope_success(client):
    agency = create_agency(client, "Scope Agency A", "admin_a@scopeagency.com")
    setup = create_project_with_scope(client, agency["headers"])

    mock_ai = MockAIService(
        classification="In scope",
        reason="The contact form is explicitly listed under included scope items.",
        client_reply="Certainly! We will build the contact form as part of your project.",
    )
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        response = client.post(
            "/api/v1/requests/check",
            json={
                "project_id": setup["project_id"],
                "client_request": "Please build a contact form on the home page.",
            },
            headers=agency["headers"],
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["classification"] == "In scope"
        assert "contact form" in data["reason"].lower()
        assert "Certainly!" in data["client_reply"]
        assert data["project_id"] == setup["project_id"]
        assert data["workspace_id"] == agency["workspace_id"]
        assert data["project_name"] == "Website Redesign"
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 2: Successful "Out of scope" classification
def test_check_request_out_of_scope_success(client):
    agency = create_agency(client, "Scope Agency B", "admin_b@scopeagency.com")
    setup = create_project_with_scope(client, agency["headers"])

    mock_ai = MockAIService(
        classification="Out of scope",
        reason="Hindi translations are explicitly documented in not-included scope.",
        client_reply="We'd love to help with Hindi translations, but this falls outside our agreed scope. Would you like a quote?",
    )
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        response = client.post(
            "/api/v1/requests/check",
            json={
                "project_id": setup["project_id"],
                "client_request": "Can you provide Hindi translations for all pages?",
            },
            headers=agency["headers"],
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["classification"] == "Out of scope"
        assert "not-included" in data["reason"].lower()
        assert "outside our agreed scope" in data["client_reply"].lower()
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 3: Successful "Not sure" classification
def test_check_request_not_sure_success(client):
    agency = create_agency(client, "Scope Agency C", "admin_c@scopeagency.com")
    setup = create_project_with_scope(client, agency["headers"])

    mock_ai = MockAIService(
        classification="Not sure",
        reason="The scope does not specify any requirements regarding newsletter integrations.",
        client_reply="Thank you for your request. Let's schedule a brief call to clarify whether this can be included.",
    )
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        response = client.post(
            "/api/v1/requests/check",
            json={
                "project_id": setup["project_id"],
                "client_request": "Connect our Mailchimp newsletter list.",
            },
            headers=agency["headers"],
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["classification"] == "Not sure"
        assert "newsletter" in data["reason"].lower()
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 4: Saving requests and AI answers in PostgreSQL (database verification)
def test_request_persisted_in_database(client, db_session):
    agency = create_agency(client, "Persistence Agency", "persist@agency.com")
    setup = create_project_with_scope(client, agency["headers"])

    mock_ai = MockAIService(
        classification="In scope",
        reason="Explicitly covered.",
        client_reply="Confirmed.",
    )
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        req_text = "Please make the mobile layout responsive."
        resp = client.post(
            "/api/v1/requests/check",
            json={
                "project_id": setup["project_id"],
                "client_request": req_text,
            },
            headers=agency["headers"],
        )
        assert resp.status_code == status.HTTP_201_CREATED
        req_id = resp.json()["id"]

        # Directly query the database to verify persistence
        saved_req = db_session.query(Request).filter(Request.id == uuid.UUID(req_id)).first()
        assert saved_req is not None
        assert saved_req.client_request == req_text
        assert saved_req.classification == "In scope"
        assert saved_req.reason == "Explicitly covered."
        assert saved_req.client_reply == "Confirmed."
        assert str(saved_req.workspace_id) == agency["workspace_id"]
        assert str(saved_req.user_id) == agency["user_id"]
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 5: Retrieving request history (GET /api/v1/requests and filtered by ?project_id=...)
def test_list_requests_and_filter_by_project(client):
    agency = create_agency(client, "History Agency", "history@agency.com")
    setup1 = create_project_with_scope(client, agency["headers"], project_name="Project One")
    setup2 = create_project_with_scope(client, agency["headers"], project_name="Project Two")

    mock_ai = MockAIService()
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        # Create 2 requests for project 1
        client.post(
            "/api/v1/requests/check",
            json={"project_id": setup1["project_id"], "client_request": "Request 1 for P1"},
            headers=agency["headers"],
        )
        client.post(
            "/api/v1/requests/check",
            json={"project_id": setup1["project_id"], "client_request": "Request 2 for P1"},
            headers=agency["headers"],
        )
        # Create 1 request for project 2
        client.post(
            "/api/v1/requests/check",
            json={"project_id": setup2["project_id"], "client_request": "Request 1 for P2"},
            headers=agency["headers"],
        )

        # List all requests in workspace
        all_resp = client.get("/api/v1/requests", headers=agency["headers"])
        assert all_resp.status_code == status.HTTP_200_OK
        assert len(all_resp.json()) == 3

        # Filter by project 1
        p1_resp = client.get(f"/api/v1/requests?project_id={setup1['project_id']}", headers=agency["headers"])
        assert p1_resp.status_code == status.HTTP_200_OK
        assert len(p1_resp.json()) == 2
        for item in p1_resp.json():
            assert item["project_id"] == setup1["project_id"]

        # Filter by project 2
        p2_resp = client.get(f"/api/v1/requests?project_id={setup2['project_id']}", headers=agency["headers"])
        assert p2_resp.status_code == status.HTTP_200_OK
        assert len(p2_resp.json()) == 1
        assert p2_resp.json()[0]["project_id"] == setup2["project_id"]
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 6: Retrieving an individual request by ID
def test_get_individual_request(client):
    agency = create_agency(client, "Single Request Agency", "single@agency.com")
    setup = create_project_with_scope(client, agency["headers"])

    mock_ai = MockAIService()
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        post_resp = client.post(
            "/api/v1/requests/check",
            json={"project_id": setup["project_id"], "client_request": "Specific requirement."},
            headers=agency["headers"],
        )
        req_id = post_resp.json()["id"]

        get_resp = client.get(f"/api/v1/requests/{req_id}", headers=agency["headers"])
        assert get_resp.status_code == status.HTTP_200_OK
        assert get_resp.json()["id"] == req_id
        assert get_resp.json()["client_request"] == "Specific requirement."
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 7: Invalid project reference returns 404
def test_check_request_invalid_project(client):
    agency = create_agency(client, "Invalid Agency", "invalid@agency.com")
    fake_project_id = str(uuid.uuid4())

    mock_ai = MockAIService()
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        resp = client.post(
            "/api/v1/requests/check",
            json={"project_id": fake_project_id, "client_request": "Random request"},
            headers=agency["headers"],
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        assert "project not found" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 8: Cross-workspace project access returns 404
def test_check_request_cross_workspace_isolation(client):
    agency1 = create_agency(client, "Owner Agency", "owner@agency.com")
    setup1 = create_project_with_scope(client, agency1["headers"])

    agency2 = create_agency(client, "Intruder Agency", "intruder@agency.com")

    mock_ai = MockAIService()
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        # Agency 2 attempts to check request against Agency 1's project
        resp = client.post(
            "/api/v1/requests/check",
            json={"project_id": setup1["project_id"], "client_request": "Sneaky request"},
            headers=agency2["headers"],
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

        # Agency 2 also cannot access Agency 1's evaluated request by ID
        post_owner = client.post(
            "/api/v1/requests/check",
            json={"project_id": setup1["project_id"], "client_request": "Owner request"},
            headers=agency1["headers"],
        )
        req_id = post_owner.json()["id"]

        get_resp = client.get(f"/api/v1/requests/{req_id}", headers=agency2["headers"])
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 9: Missing authentication returns 401
def test_check_request_unauthenticated(client):
    resp = client.post(
        "/api/v1/requests/check",
        json={"project_id": str(uuid.uuid4()), "client_request": "Unauthenticated check"},
    )
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# Test 10: Empty client request returns 422
def test_check_request_validation_empty_request(client):
    agency = create_agency(client, "Validation Agency", "val@agency.com")
    setup = create_project_with_scope(client, agency["headers"])

    resp = client.post(
        "/api/v1/requests/check",
        json={"project_id": setup["project_id"], "client_request": "   "},
        headers=agency["headers"],
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Test 11: AI API failure handling (mock raises AIServiceError, returns 502)
def test_check_request_ai_service_error_handling(client):
    agency = create_agency(client, "Outage Agency", "outage@agency.com")
    setup = create_project_with_scope(client, agency["headers"])

    failing_ai = MockAIService(should_raise=True)
    app.dependency_overrides[get_ai_service] = lambda: failing_ai

    try:
        resp = client.post(
            "/api/v1/requests/check",
            json={"project_id": setup["project_id"], "client_request": "Will fail"},
            headers=agency["headers"],
        )
        assert resp.status_code == status.HTTP_502_BAD_GATEWAY
        assert "AI Service Error" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 12: Ensure ONLY the selected project's scope items are passed to the AI classifier
def test_only_selected_project_scope_passed_to_ai(client):
    agency = create_agency(client, "Scope Isolation Agency", "scopeiso@agency.com")
    setup_alpha = create_project_with_scope(client, agency["headers"], project_name="Project Alpha")
    setup_beta = create_project_with_scope(client, agency["headers"], project_name="Project Beta")

    # Add extra scope item to Project Beta
    client.post(
        "/api/v1/scope-items",
        json={
            "project_id": setup_beta["project_id"],
            "included_description": "Project Beta Exclusive Scope Item",
            "not_included_description": "Project Beta Exclusive Exclusion",
        },
        headers=agency["headers"],
    )

    mock_ai = MockAIService()
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        # Check against Project Alpha
        resp = client.post(
            "/api/v1/requests/check",
            json={"project_id": setup_alpha["project_id"], "client_request": "Check Alpha"},
            headers=agency["headers"],
        )
        assert resp.status_code == status.HTTP_201_CREATED

        # Verify in mock: only Project Alpha scope items were passed
        passed_scopes = mock_ai.last_scope_items
        assert len(passed_scopes) == 1
        assert passed_scopes[0].project_id == uuid.UUID(setup_alpha["project_id"])
        assert "Project Beta Exclusive Scope Item" not in passed_scopes[0].included_description
    finally:
        app.dependency_overrides.pop(get_ai_service, None)
