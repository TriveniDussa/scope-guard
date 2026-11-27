import json
from unittest.mock import MagicMock, call, patch
import httpx
import pytest
from fastapi import status

from app.models.lesson import Lesson
from app.models.project import Project
from app.models.request import Request
from app.models.scope_item import ScopeItem
from app.services.ai.base import (
    AIClassificationResult,
    AIServiceError,
    BaseAIService,
    ClassificationEnum,
)
from app.services.ai.gemini import GeminiAIService
from backend.tests.test_requests import create_agency, create_project_with_scope


SUCCESS_JSON_RESPONSE = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": json.dumps(
                            {
                                "classification": "In scope",
                                "reason": "Explicitly included in project baseline.",
                                "client_reply": "We are on it.",
                            }
                        )
                    }
                ]
            }
        }
    ]
}


# =====================================================================
# Unit Tests for GeminiAIService Retry and Backoff
# =====================================================================

def test_gemini_retry_503_then_success():
    """Verify GeminiAIService retries HTTP 503 once and succeeds with 2s delay."""
    service = GeminiAIService(api_key="test_key", model="gemini-3.8-flash")

    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.text = "503 UNAVAILABLE: The model is overloaded"

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = SUCCESS_JSON_RESPONSE

    with patch("httpx.Client.post", side_effect=[mock_resp_503, mock_resp_200]) as mock_post, \
         patch("time.sleep") as mock_sleep:
        result = service.classify_request("Build landing page", [])

        assert result.classification == ClassificationEnum.IN_SCOPE
        assert result.reason == "Explicitly included in project baseline."
        assert mock_post.call_count == 2
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(2.0)


def test_gemini_retry_503_two_retries_then_success():
    """Verify GeminiAIService retries HTTP 503 twice (2s then 4s) and succeeds on 3rd attempt."""
    service = GeminiAIService(api_key="test_key", model="gemini-3.8-flash")

    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.text = "503 UNAVAILABLE: High demand"

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = SUCCESS_JSON_RESPONSE

    with patch("httpx.Client.post", side_effect=[mock_resp_503, mock_resp_503, mock_resp_200]) as mock_post, \
         patch("time.sleep") as mock_sleep:
        result = service.classify_request("Build landing page", [])

        assert result.classification == ClassificationEnum.IN_SCOPE
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(2.0), call(4.0)])


def test_gemini_retry_503_exhausted_raises_temporary_error():
    """Verify GeminiAIService retries max 2 times on repeated 503 and raises clear temporary error."""
    service = GeminiAIService(api_key="test_key", model="gemini-3.8-flash")

    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.text = "503 UNAVAILABLE: Server temporarily overloaded"

    with patch("httpx.Client.post", side_effect=[mock_resp_503, mock_resp_503, mock_resp_503]) as mock_post, \
         patch("time.sleep") as mock_sleep:
        with pytest.raises(AIServiceError) as exc_info:
            service.classify_request("Build landing page", [])

        err = exc_info.value
        assert err.is_temporary is True
        assert err.status_code == 503
        assert "temporarily unavailable" in err.message.lower()
        assert mock_post.call_count == 3  # 1 initial + 2 retries
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(2.0), call(4.0)])


def test_gemini_retry_timeout_then_success():
    """Verify GeminiAIService retries on transient network timeout and succeeds."""
    service = GeminiAIService(api_key="test_key", model="gemini-3.8-flash")

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = SUCCESS_JSON_RESPONSE

    timeout_exc = httpx.ReadTimeout("Connection timed out after 30s")

    with patch("httpx.Client.post", side_effect=[timeout_exc, mock_resp_200]) as mock_post, \
         patch("time.sleep") as mock_sleep:
        result = service.classify_request("Build landing page", [])

        assert result.classification == ClassificationEnum.IN_SCOPE
        assert mock_post.call_count == 2
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(2.0)


def test_gemini_retry_timeout_exhausted():
    """Verify GeminiAIService retries max 2 times on repeated timeouts and raises clear temporary error."""
    service = GeminiAIService(api_key="test_key", model="gemini-3.8-flash")

    timeout_exc = httpx.ReadTimeout("Connection timed out after 30s")

    with patch("httpx.Client.post", side_effect=[timeout_exc, timeout_exc, timeout_exc]) as mock_post, \
         patch("time.sleep") as mock_sleep:
        with pytest.raises(AIServiceError) as exc_info:
            service.classify_request("Build landing page", [])

        err = exc_info.value
        assert err.is_temporary is True
        assert err.status_code == 503
        assert "temporarily unreachable due to network timeouts" in err.message.lower()
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(2.0), call(4.0)])


@pytest.mark.parametrize(
    "status_code,err_text,expected_phrase",
    [
        (400, "INVALID_ARGUMENT: Bad JSON syntax", "malformed request"),
        (401, "API_KEY_INVALID: Key not found", "authentication failed"),
        (403, "PERMISSION_DENIED: Access restricted", "authentication failed"),
        (404, "NOT_FOUND: Model not found", "not found"),
        (429, "RESOURCE_EXHAUSTED: Rate limit exceeded", "rate limit exceeded"),
    ],
)
def test_gemini_permanent_errors_do_not_retry(status_code, err_text, expected_phrase):
    """Verify permanent errors (400, 401, 403, 404, 429) fail immediately without retrying."""
    service = GeminiAIService(api_key="test_key", model="gemini-3.8-flash")

    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = err_text

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post, \
         patch("time.sleep") as mock_sleep:
        with pytest.raises(AIServiceError) as exc_info:
            service.classify_request("Build landing page", [])

        assert expected_phrase in str(exc_info.value).lower()
        # Ensure it failed immediately on the 1st attempt: 0 retries, 0 sleep calls
        assert mock_post.call_count == 1
        assert mock_sleep.call_count == 0


# =====================================================================
# Integration / Endpoint Tests: HTTP 503 and No Duplicate Records
# =====================================================================

def test_endpoint_check_temporary_unavailability_returns_503_and_no_duplicate_records(client, db_session):
    """
    Verify /api/v1/requests/check returns HTTP 503 when AI service fails with 503,
    and verify NO request or lesson records are stored in the database.
    """
    agency = create_agency(client, "Retry Agency", "admin@retryagency.com")
    project_data = create_project_with_scope(client, agency["headers"], "E-commerce App")

    initial_request_count = db_session.query(Request).count()
    initial_lesson_count = db_session.query(Lesson).count()

    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.text = "503 UNAVAILABLE: High demand"

    orig_post = httpx.Client.post

    def selective_post(self_client, url, *args, **kwargs):
        if "googleapis.com" in str(url):
            return mock_resp_503
        return orig_post(self_client, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=selective_post), \
         patch("time.sleep"):
        resp = client.post(
            "/api/v1/requests/check",
            json={
                "project_id": project_data["project_id"],
                "client_request": "Add cryptocurrency payment gateway",
            },
            headers=agency["headers"],
        )

    # Must return HTTP 503 Service Unavailable, NOT 502
    assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = resp.json()
    assert "temporarily unavailable" in data["detail"].lower()

    # Crucial Verification: ZERO new records created during failed attempts
    assert db_session.query(Request).count() == initial_request_count
    assert db_session.query(Lesson).count() == initial_lesson_count


def test_endpoint_check_retry_success_creates_single_record(client, db_session):
    """
    Verify /api/v1/requests/check succeeds after a transient 503 retry,
    and stores exactly ONE request record.
    """
    agency = create_agency(client, "Single Record Agency", "admin@singlerecord.com")
    project_data = create_project_with_scope(client, agency["headers"], "Portal App")

    initial_request_count = db_session.query(Request).count()

    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.text = "503 UNAVAILABLE"

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = SUCCESS_JSON_RESPONSE

    responses = [mock_resp_503, mock_resp_200]
    call_records = []
    orig_post = httpx.Client.post

    def selective_post(self_client, url, *args, **kwargs):
        if "googleapis.com" in str(url):
            call_records.append(url)
            return responses.pop(0) if responses else mock_resp_200
        return orig_post(self_client, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=selective_post), \
         patch("time.sleep"):
        resp = client.post(
            "/api/v1/requests/check",
            json={
                "project_id": project_data["project_id"],
                "client_request": "Homepage design layout",
            },
            headers=agency["headers"],
        )

    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["classification"] == "In scope"

    # Exactly 1 new record was added
    assert db_session.query(Request).count() == initial_request_count + 1
    assert len(call_records) == 2


def test_endpoint_check_again_temporary_unavailability_preserves_records(client, db_session):
    """
    Verify /api/v1/requests/{id}/check-again returns HTTP 503 on exhausted 503,
    and preserves the existing request without creating a duplicate.
    """
    agency = create_agency(client, "Check Again Agency", "admin@checkagain.com")
    project_data = create_project_with_scope(client, agency["headers"], "Mobile App")

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = SUCCESS_JSON_RESPONSE

    mock_resp_503 = MagicMock()
    mock_resp_503.status_code = 503
    mock_resp_503.text = "503 UNAVAILABLE"

    current_gemini_resp = [mock_resp_200]
    orig_post = httpx.Client.post

    def selective_post(self_client, url, *args, **kwargs):
        if "googleapis.com" in str(url):
            return current_gemini_resp[0]
        return orig_post(self_client, url, *args, **kwargs)

    # 1. Create initial successful request
    with patch.object(httpx.Client, "post", new=selective_post):
        initial_check = client.post(
            "/api/v1/requests/check",
            json={
                "project_id": project_data["project_id"],
                "client_request": "Design initial mockup",
            },
            headers=agency["headers"],
        )
    assert initial_check.status_code == status.HTTP_201_CREATED
    req_id = initial_check.json()["id"]

    request_count_before = db_session.query(Request).count()

    # 2. Trigger check-again while Gemini is returning 503
    current_gemini_resp[0] = mock_resp_503
    with patch.object(httpx.Client, "post", new=selective_post), \
         patch("time.sleep"):
        again_resp = client.post(
            f"/api/v1/requests/{req_id}/check-again",
            headers=agency["headers"],
        )

    assert again_resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "temporarily unavailable" in again_resp.json()["detail"].lower()

    # Total requests count must remain unchanged (no orphan record added)
    assert db_session.query(Request).count() == request_count_before
