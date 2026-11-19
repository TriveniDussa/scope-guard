from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    email: Optional[EmailStr] = Field(None, description="Primary contact email")


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Client name")
    email: Optional[EmailStr] = Field(None, description="Primary contact email")


class ClientRead(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
