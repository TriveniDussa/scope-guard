import json
import pytest
from unittest.mock import MagicMock, patch
import httpx
from fastapi import status

from app.core.config import Settings
from app.services.ai.base import AIServiceError
from app.services.ai.gemini import GeminiAIService


def test_health_check_endpoint(client):
    """Verify that GET /health returns the exact expected production format."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(client):
    """Verify that GET / returns the application overview."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "online"
    assert "/docs" in data["docs"]


def test_cors_origins_parsing():
    """Verify that CORS origins are parsed, cleaned, and sorted correctly."""
    custom_settings = Settings(
        CORS_ORIGINS="https://scope-guard.vercel.app/, http://localhost:5173, https://app.example.com  "
    )
    origins = custom_settings.get_cors_origins()
    assert "https://scope-guard.vercel.app" in origins
    assert "http://localhost:5173" in origins
    assert "https://app.example.com" in origins
    # Ensure no trailing slashes
    for o in origins:
        assert not o.endswith("/")


def test_gemini_service_defaults_to_supported_model():
    """Verify GeminiAIService uses the current supported production model."""
    service = GeminiAIService(api_key="test_key")
    assert service.model == "gemini-2.5-flash"


def test_gemini_service_strips_markdown_code_fences():
    """Verify GeminiAIService strips ```json code fences if returned by the LLM."""
    service = GeminiAIService(api_key="test_key", model="gemini-2.5-flash")

    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": "```json\n{\n  \"classification\": \"In scope\",\n  \"reason\": \"Included in deliverables\",\n  \"client_reply\": \"We are working on it\"\n}\n```"
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch("httpx.Client.post", return_value=mock_resp):
        result = service.classify_request("Build landing page", [])
        assert result.classification.value == "In scope"
        assert result.reason == "Included in deliverables"
        assert result.client_reply == "We are working on it"


def test_gemini_service_rate_limit_error_handling():
    """Verify GeminiAIService raises a clear AIServiceError on HTTP 429 Rate Limit."""
    service = GeminiAIService(api_key="test_key", model="gemini-2.5-flash")

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "RESOURCE_EXHAUSTED: Rate limit exceeded"

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(AIServiceError) as exc_info:
            service.classify_request("Build landing page", [])
        assert "rate limit exceeded" in str(exc_info.value).lower()
