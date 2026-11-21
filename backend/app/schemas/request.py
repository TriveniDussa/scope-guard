from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RequestCheckIn(BaseModel):
    project_id: UUID = Field(..., description="Project to evaluate the request against")
    client_request: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The client's request description to check against the scope baseline",
    )

    @field_validator("client_request")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Client request cannot be empty or whitespace only")
        return v.strip()


class FeedbackEnum(str, Enum):
    RIGHT = "Right"
    WRONG = "Wrong"


class CorrectResultEnum(str, Enum):
    IN_SCOPE = "In scope"
    OUT_OF_SCOPE = "Out of scope"


class RequestFeedbackIn(BaseModel):
    feedback: FeedbackEnum = Field(..., description="'Right' or 'Wrong'")
    correct_result: Optional[CorrectResultEnum] = Field(
        None,
        description="Required if feedback is 'Wrong': 'In scope' or 'Out of scope'",
    )
    correction_reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="Required if feedback is 'Wrong': meaningful explanation justifying the correction",
    )

    @model_validator(mode="after")
    def validate_feedback_rules(self):
        if self.feedback == FeedbackEnum.WRONG:
            if not self.correct_result:
                raise ValueError("correct_result is required when feedback is 'Wrong'")
            if not self.correction_reason or not self.correction_reason.strip():
                raise ValueError("correction_reason is required when feedback is 'Wrong'")
            self.correction_reason = self.correction_reason.strip()
        return self


class RequestRead(BaseModel):
    id: UUID
    workspace_id: UUID
    project_id: UUID
    user_id: Optional[UUID] = None
    parent_request_id: Optional[UUID] = None
    client_request: str
    classification: str
    reason: str
    client_reply: str
    feedback: Optional[str] = None
    project_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckAgainResponse(BaseModel):
    old_answer: RequestRead
    new_answer: RequestRead
