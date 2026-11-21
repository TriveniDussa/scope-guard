from app.core.config import settings
from app.services.ai.base import BaseAIService
from app.services.ai.gemini import GeminiAIService


def get_ai_service() -> BaseAIService:
    """
    Factory dependency providing the configured AI Service provider.
    Defaults to GeminiAIService, modularly replaceable or overridable in tests.
    """
    provider = settings.AI_PROVIDER.lower().strip()
    if provider == "gemini":
        return GeminiAIService()
    # Placeholder for OpenAI or other providers when approved
    return GeminiAIService()
