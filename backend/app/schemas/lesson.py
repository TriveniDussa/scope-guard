from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class LessonRead(BaseModel):
    id: UUID
    workspace_id: UUID
    project_id: UUID
    request_id: Optional[UUID] = None
    ai_answer: str = Field(..., description="The original AI classification on the request")
    correct_result: str = Field(..., description="'In scope' or 'Out of scope'")
    correction_reason: str = Field(..., description="Human agency explanation justifying the correction")
    project_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
