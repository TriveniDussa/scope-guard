from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ScopeItemBase(BaseModel):
    project_id: UUID = Field(..., description="Project ID to which this scope item belongs")
    included_description: str = Field(..., min_length=1, description="Explicitly contracted / included deliverables")
    not_included_description: str = Field(..., min_length=1, description="Explicitly excluded / out-of-scope deliverables")


class ScopeItemCreate(ScopeItemBase):
    pass


class ScopeItemUpdate(BaseModel):
    project_id: Optional[UUID] = Field(None, description="Project ID if moving to another project")
    included_description: Optional[str] = Field(None, min_length=1, description="Updated included deliverables")
    not_included_description: Optional[str] = Field(None, min_length=1, description="Updated excluded deliverables")


class ScopeItemRead(BaseModel):
    id: UUID
    workspace_id: UUID
    project_id: UUID
    included_description: str
    not_included_description: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
