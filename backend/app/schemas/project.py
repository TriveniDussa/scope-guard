from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectStatus(str, Enum):
    ACTIVE = "Active"
    DONE = "Done"


class ProjectBase(BaseModel):
    client_id: UUID = Field(..., description="ID of the client that owns this project")
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    status: ProjectStatus = Field(default=ProjectStatus.ACTIVE, description="Project status: Active or Done")

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower == "active":
                return ProjectStatus.ACTIVE
            if v_lower == "done":
                return ProjectStatus.DONE
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    client_id: Optional[UUID] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[ProjectStatus] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower == "active":
                return ProjectStatus.ACTIVE
            if v_lower == "done":
                return ProjectStatus.DONE
        return v


class ProjectRead(BaseModel):
    id: UUID
    workspace_id: UUID
    client_id: UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
