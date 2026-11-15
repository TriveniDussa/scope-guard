from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.workspace import WorkspaceRead


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    role: Optional[str] = "admin"


class UserRead(UserBase):
    id: UUID
    workspace_id: UUID
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgencySignupRequest(BaseModel):
    agency_name: str = Field(..., min_length=2, max_length=255, description="Agency / Company name")
    email: EmailStr = Field(..., description="Agency Admin Email")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Agency Owner/Admin full name")


class AgencySignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
    workspace: WorkspaceRead
