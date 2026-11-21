import json
import logging
from typing import Any, List
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.services.ai.base import (
    AIClassificationResult,
    AIServiceError,
    BaseAIService,
    ClassificationEnum,
)
from app.services.ai.prompt import SYSTEM_INSTRUCTION, build_classification_prompt

logger = logging.getLogger(__name__)


class GeminiAIService(BaseAIService):
    """
    Google Gemini API implementation using the official Generative Language REST API.
    Utilizes structured JSON output enforcement.
    """
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.AI_MODEL or "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def classify_request(
        self,
        client_request: str,
        scope_items: List[Any],
    ) -> AIClassificationResult:
        if not self.api_key or self.api_key.strip() in ("", "your_gemini_api_key_here"):
            raise AIServiceError("GEMINI_API_KEY is not configured in environment variables.")

        user_prompt = build_classification_prompt(client_request, scope_items)

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,  # Low temperature for strict determinism
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)

            if response.status_code != 200:
                err_text = response.text
                logger.error(f"Gemini API returned status {response.status_code}: {err_text}")
                raise AIServiceError(
                    f"Gemini API error ({response.status_code}): {err_text}",
                    original_error=err_text,
                )

            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if not candidates:
                raise AIServiceError("Gemini API returned no response candidates.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                raise AIServiceError("Gemini API returned an empty response part.")

            raw_text = parts[0].get("text", "").strip()
            parsed_data = json.loads(raw_text)

            # Validate structured model
            return AIClassificationResult.model_validate(parsed_data)

        except (httpx.RequestError, httpx.TimeoutException) as exc:
            logger.error(f"Network error calling Gemini API: {exc}")
            raise AIServiceError("Network error while connecting to Gemini API.", original_error=exc)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse JSON response from Gemini API: {exc}")
            raise AIServiceError("Gemini API did not return valid JSON.", original_error=exc)
        except ValidationError as exc:
            logger.error(f"AI response did not match expected schema: {exc}")
            raise AIServiceError("AI response failed schema validation.", original_error=exc)
        except AIServiceError:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in GeminiAIService: {exc}")
            raise AIServiceError(f"Unexpected error during AI evaluation: {str(exc)}", original_error=exc)
