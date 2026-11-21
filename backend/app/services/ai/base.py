from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List
from pydantic import BaseModel, Field


class ClassificationEnum(str, Enum):
    IN_SCOPE = "In scope"
    OUT_OF_SCOPE = "Out of scope"
    NOT_SURE = "Not sure"


class AIClassificationResult(BaseModel):
    classification: ClassificationEnum = Field(..., description="Exact classification: In scope, Out of scope, or Not sure")
    reason: str = Field(..., description="Concise explanation justifying the classification based solely on agreed scope")
    client_reply: str = Field(..., description="Courteous and professional response draft to send to the client")


class AIServiceError(Exception):
    """Exception raised when an AI service provider call fails."""
    def __init__(self, message: str, original_error: Any = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class BaseAIService(ABC):
    """
    Abstract interface for modular AI providers (Gemini, OpenAI, etc.).
    """
    @abstractmethod
    def classify_request(
        self,
        client_request: str,
        scope_items: List[Any],
    ) -> AIClassificationResult:
        """
        Classifies whether client_request is 'In scope', 'Out of scope', or 'Not sure'
        based strictly on the provided scope_items.
        """
        pass
