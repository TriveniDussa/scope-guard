import uuid
import pytest
from fastapi import status

from app.main import app
from app.models.lesson import Lesson
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
        reason: str = "Based on scope deliverables.",
        client_reply: str = "We will handle this for you.",
        should_raise: bool = False,
    ):
        self.classification = classification
        self.reason = reason
        self.client_reply = client_reply
        self.should_raise = should_raise
        self.last_client_request = None
        self.last_scope_items = None
        self.last_lessons = None

    def classify_request(
        self,
        client_request: str,
        scope_items: list,
        lessons: list = None,
    ) -> AIClassificationResult:
        if self.should_raise:
            raise AIServiceError("Simulated AI provider failure")
        self.last_client_request = client_request
        self.last_scope_items = scope_items
        self.last_lessons = lessons or []
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


def create_project_and_request(
    client,
    agency_headers,
    project_name="Web Portal",
    client_request="Build interactive contact form",
    initial_classification="Out of scope",
):
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

    client.post(
        "/api/v1/scope-items",
        json={
            "project_id": project_id,
            "included_description": "Homepage, contact form, user login",
            "not_included_description": "Custom CRM integrations, multi-language version",
        },
        headers=agency_headers,
    )

    mock_ai = MockAIService(
        classification=initial_classification,
        reason="Initial AI analysis.",
        client_reply="Initial reply draft.",
    )
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        req_resp = client.post(
            "/api/v1/requests/check",
            json={"project_id": project_id, "client_request": client_request},
            headers=agency_headers,
        )
        assert req_resp.status_code == status.HTTP_201_CREATED
        req_data = req_resp.json()
        return {
            "project_id": project_id,
            "request_id": req_data["id"],
            "request_data": req_data,
        }
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 1: Right feedback
def test_submit_right_feedback_success(client, db_session):
    agency = create_agency(client, "Right Feedback Agency", "right@agency.com")
    setup = create_project_and_request(client, agency["headers"], initial_classification="In scope")

    resp = client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={"feedback": "Right"},
        headers=agency["headers"],
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["feedback"] == "Right"

    # Verify no lesson was created for Right feedback
    lessons_count = (
        db_session.query(Lesson)
        .filter(Lesson.request_id == uuid.UUID(setup["request_id"]))
        .count()
    )
    assert lessons_count == 0


# Test 2: Wrong feedback with correction creates lesson
def test_submit_wrong_feedback_success(client, db_session):
    agency = create_agency(client, "Wrong Feedback Agency", "wrong@agency.com")
    setup = create_project_and_request(client, agency["headers"], initial_classification="Out of scope")

    correction_reason = "The contact form is explicitly included in the agreed deliverables."
    resp = client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={
            "feedback": "Wrong",
            "correct_result": "In scope",
            "correction_reason": correction_reason,
        },
        headers=agency["headers"],
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["feedback"] == "Wrong"

    # Verify lesson was created
    lesson = (
        db_session.query(Lesson)
        .filter(Lesson.request_id == uuid.UUID(setup["request_id"]))
        .first()
    )
    assert lesson is not None
    assert lesson.ai_answer == "Out of scope"
    assert lesson.correct_result == "In scope"
    assert lesson.correction_reason == correction_reason
    assert str(lesson.workspace_id) == agency["workspace_id"]
    assert str(lesson.project_id) == setup["project_id"]


# Test 3: Missing correction result when feedback is Wrong returns 422
def test_wrong_feedback_missing_correct_result(client):
    agency = create_agency(client, "Missing Result Agency", "missing_result@agency.com")
    setup = create_project_and_request(client, agency["headers"])

    resp = client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={
            "feedback": "Wrong",
            "correction_reason": "Reason without correct_result",
        },
        headers=agency["headers"],
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Test 4: Missing correction reason when feedback is Wrong returns 422
def test_wrong_feedback_missing_correction_reason(client):
    agency = create_agency(client, "Missing Reason Agency", "missing_reason@agency.com")
    setup = create_project_and_request(client, agency["headers"])

    # Blank / whitespace only
    resp = client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={
            "feedback": "Wrong",
            "correct_result": "In scope",
            "correction_reason": "   ",
        },
        headers=agency["headers"],
    )
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Test 5: Lesson persistence in database and retrieval via GET /lessons
def test_lesson_persistence_and_listing(client):
    agency = create_agency(client, "Persistence Agency", "persist_lesson@agency.com")
    setup = create_project_and_request(client, agency["headers"], initial_classification="Not sure")

    # Submit Wrong feedback
    client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={
            "feedback": "Wrong",
            "correct_result": "Out of scope",
            "correction_reason": "Custom CRM integration is explicitly excluded in not-included scope.",
        },
        headers=agency["headers"],
    )

    # Fetch lessons list
    resp = client.get("/api/v1/lessons", headers=agency["headers"])
    assert resp.status_code == status.HTTP_200_OK
    lessons = resp.json()
    assert len(lessons) >= 1
    target = next((l for l in lessons if l["request_id"] == setup["request_id"]), None)
    assert target is not None
    assert target["ai_answer"] == "Not sure"
    assert target["correct_result"] == "Out of scope"
    assert "Custom CRM integration" in target["correction_reason"]
    assert target["project_id"] == setup["project_id"]

    # Fetch individual lesson by ID
    single_resp = client.get(f"/api/v1/lessons/{target['id']}", headers=agency["headers"])
    assert single_resp.status_code == status.HTTP_200_OK
    assert single_resp.json()["id"] == target["id"]


# Test 6: Lesson workspace isolation
def test_lesson_workspace_isolation(client):
    agency1 = create_agency(client, "Tenant 1", "tenant1@lessons.com")
    setup1 = create_project_and_request(client, agency1["headers"])

    client.post(
        f"/api/v1/requests/{setup1['request_id']}/feedback",
        json={
            "feedback": "Wrong",
            "correct_result": "In scope",
            "correction_reason": "Tenant 1 specific correction rule.",
        },
        headers=agency1["headers"],
    )

    # Get lesson id
    t1_lessons = client.get("/api/v1/lessons", headers=agency1["headers"]).json()
    lesson1_id = t1_lessons[0]["id"]

    # Agency 2 attempts to list lessons and get lesson by ID
    agency2 = create_agency(client, "Tenant 2", "tenant2@lessons.com")
    t2_resp = client.get("/api/v1/lessons", headers=agency2["headers"])
    assert t2_resp.status_code == status.HTTP_200_OK
    assert len(t2_resp.json()) == 0

    get_single = client.get(f"/api/v1/lessons/{lesson1_id}", headers=agency2["headers"])
    assert get_single.status_code == status.HTTP_404_NOT_FOUND


# Test 7: Lesson project isolation (filter by project_id)
def test_lesson_project_isolation(client):
    agency = create_agency(client, "Multi Project Agency", "multiproject@agency.com")
    setup_p1 = create_project_and_request(client, agency["headers"], project_name="Project Alpha")
    setup_p2 = create_project_and_request(client, agency["headers"], project_name="Project Beta")

    # Add feedback to both
    client.post(
        f"/api/v1/requests/{setup_p1['request_id']}/feedback",
        json={"feedback": "Wrong", "correct_result": "In scope", "correction_reason": "Alpha rule"},
        headers=agency["headers"],
    )
    client.post(
        f"/api/v1/requests/{setup_p2['request_id']}/feedback",
        json={"feedback": "Wrong", "correct_result": "Out of scope", "correction_reason": "Beta rule"},
        headers=agency["headers"],
    )

    # Filter by Project Alpha
    alpha_resp = client.get(f"/api/v1/lessons?project_id={setup_p1['project_id']}", headers=agency["headers"])
    assert alpha_resp.status_code == status.HTTP_200_OK
    alpha_lessons = alpha_resp.json()
    assert len(alpha_lessons) == 1
    assert alpha_lessons[0]["project_id"] == setup_p1["project_id"]
    assert alpha_lessons[0]["correction_reason"] == "Alpha rule"


# Test 8: AI receives relevant lessons
def test_ai_receives_relevant_lessons_on_check_again(client):
    agency = create_agency(client, "AI Context Agency", "aicontext@agency.com")
    setup = create_project_and_request(
        client,
        agency["headers"],
        client_request="Integrate payment gateway",
        initial_classification="In scope",
    )

    # Human correction says it's Out of scope
    client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={
            "feedback": "Wrong",
            "correct_result": "Out of scope",
            "correction_reason": "Payment gateways require third-party compliance and are excluded.",
        },
        headers=agency["headers"],
    )

    # Setup mock to inspect received lessons during Check Again
    mock_ai = MockAIService(
        classification="Out of scope",
        reason="Corrected based on learned agency lesson.",
        client_reply="We'd love to help with the payment gateway as an add-on proposal.",
    )
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        resp = client.post(
            f"/api/v1/requests/{setup['request_id']}/check-again",
            headers=agency["headers"],
        )
        assert resp.status_code == status.HTTP_201_CREATED
        # Verify that mock received the lesson
        assert len(mock_ai.last_lessons) == 1
        assert mock_ai.last_lessons[0].correct_result == "Out of scope"
        assert "Payment gateways" in mock_ai.last_lessons[0].correction_reason
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 9: AI does not receive another workspace's lessons
def test_ai_does_not_receive_cross_workspace_lessons(client):
    # Agency 1 creates a lesson
    agency1 = create_agency(client, "Agency One", "agency1@iso.com")
    setup1 = create_project_and_request(client, agency1["headers"])
    client.post(
        f"/api/v1/requests/{setup1['request_id']}/feedback",
        json={"feedback": "Wrong", "correct_result": "In scope", "correction_reason": "Agency 1 secret rule"},
        headers=agency1["headers"],
    )

    # Agency 2 checks a request on their own project
    agency2 = create_agency(client, "Agency Two", "agency2@iso.com")
    setup2 = create_project_and_request(client, agency2["headers"])

    mock_ai = MockAIService()
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        client.post(
            f"/api/v1/requests/{setup2['request_id']}/check-again",
            headers=agency2["headers"],
        )
        # Agency 2's AI call should have 0 lessons
        assert len(mock_ai.last_lessons) == 0
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 10: Check Again returns old and new answers
def test_check_again_returns_old_and_new_answers(client):
    agency = create_agency(client, "Comparison Agency", "compare@agency.com")
    setup = create_project_and_request(
        client,
        agency["headers"],
        client_request="Can you build an admin dashboard?",
        initial_classification="Not sure",
    )

    # Submit correction
    client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={"feedback": "Wrong", "correct_result": "In scope", "correction_reason": "Admin dashboard was included in addendum."},
        headers=agency["headers"],
    )

    mock_ai = MockAIService(
        classification="In scope",
        reason="Updated to In scope per agency lesson guidance.",
        client_reply="We will include the admin dashboard in the current sprint.",
    )
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        resp = client.post(
            f"/api/v1/requests/{setup['request_id']}/check-again",
            headers=agency["headers"],
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "old_answer" in data
        assert "new_answer" in data

        old_ans = data["old_answer"]
        new_ans = data["new_answer"]

        assert old_ans["classification"] == "Not sure"
        assert new_ans["classification"] == "In scope"
        assert old_ans["id"] == setup["request_id"]
        assert new_ans["id"] != setup["request_id"]
        assert new_ans["parent_request_id"] == setup["request_id"]
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 11: Original answer remains unchanged
def test_original_answer_remains_unchanged(client):
    agency = create_agency(client, "Immutability Agency", "immutable@agency.com")
    setup = create_project_and_request(client, agency["headers"], initial_classification="Out of scope")

    original_classification = setup["request_data"]["classification"]
    original_reason = setup["request_data"]["reason"]

    mock_ai = MockAIService(classification="In scope", reason="New evaluation reason.")
    app.dependency_overrides[get_ai_service] = lambda: mock_ai

    try:
        # Run Check Again
        client.post(
            f"/api/v1/requests/{setup['request_id']}/check-again",
            headers=agency["headers"],
        )

        # Retrieve original request and confirm it was NOT altered
        orig_resp = client.get(
            f"/api/v1/requests/{setup['request_id']}",
            headers=agency["headers"],
        )
        assert orig_resp.status_code == status.HTTP_200_OK
        data = orig_resp.json()
        assert data["classification"] == original_classification
        assert data["reason"] == original_reason
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Test 12: Unauthenticated requests return 401
def test_unauthenticated_requests(client):
    fake_id = str(uuid.uuid4())

    # Feedback
    fb_resp = client.post(f"/api/v1/requests/{fake_id}/feedback", json={"feedback": "Right"})
    assert fb_resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Check Again
    ca_resp = client.post(f"/api/v1/requests/{fake_id}/check-again")
    assert ca_resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Lessons
    ls_resp = client.get("/api/v1/lessons")
    assert ls_resp.status_code == status.HTTP_401_UNAUTHORIZED


# Test 13: Invalid request IDs return 404
def test_invalid_request_id_returns_404(client):
    agency = create_agency(client, "404 Agency", "notfound@agency.com")
    fake_id = str(uuid.uuid4())

    # Feedback on non-existent request
    fb_resp = client.post(
        f"/api/v1/requests/{fake_id}/feedback",
        json={"feedback": "Right"},
        headers=agency["headers"],
    )
    assert fb_resp.status_code == status.HTTP_404_NOT_FOUND

    # Check Again on non-existent request
    ca_resp = client.post(
        f"/api/v1/requests/{fake_id}/check-again",
        headers=agency["headers"],
    )
    assert ca_resp.status_code == status.HTTP_404_NOT_FOUND


# Test 14: AI failure handling during Check Again returns 502
def test_check_again_ai_failure_handling(client):
    agency = create_agency(client, "Outage Check Again Agency", "outage_ca@agency.com")
    setup = create_project_and_request(client, agency["headers"])

    failing_ai = MockAIService(should_raise=True)
    app.dependency_overrides[get_ai_service] = lambda: failing_ai

    try:
        resp = client.post(
            f"/api/v1/requests/{setup['request_id']}/check-again",
            headers=agency["headers"],
        )
        assert resp.status_code == status.HTTP_502_BAD_GATEWAY
        assert "AI Service Error" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_ai_service, None)


# Bonus Test 15: Duplicate feedback prevention returns 400
def test_duplicate_feedback_prevention(client):
    agency = create_agency(client, "Duplicate Prevention Agency", "duplicate@agency.com")
    setup = create_project_and_request(client, agency["headers"])

    # First feedback succeeds
    resp1 = client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={"feedback": "Right"},
        headers=agency["headers"],
    )
    assert resp1.status_code == status.HTTP_200_OK

    # Second feedback is rejected with 400
    resp2 = client.post(
        f"/api/v1/requests/{setup['request_id']}/feedback",
        json={"feedback": "Right"},
        headers=agency["headers"],
    )
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been submitted" in resp2.json()["detail"].lower()
