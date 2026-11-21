from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class RequestRead(BaseModel):
    id: UUID
    workspace_id: UUID
    project_id: UUID
    user_id: Optional[UUID] = None
    client_request: str
    classification: str
    reason: str
    client_reply: str
    project_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
