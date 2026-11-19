from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    TO_DO = "To do"
    DOING = "Doing"
    DONE = "Done"


class TaskBase(BaseModel):
    project_id: UUID = Field(..., description="Project to which this task belongs")
    scope_item_id: UUID = Field(..., description="Scope item deliverable to which this task is linked")
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    due_date: Optional[date] = Field(None, description="Due date in YYYY-MM-DD format")
    status: TaskStatus = Field(default=TaskStatus.TO_DO, description="Task status (To do, Doing, Done)")

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in ("to do", "todo"):
                return TaskStatus.TO_DO
            if clean in ("doing", "in_progress", "in progress"):
                return TaskStatus.DOING
            if clean == "done":
                return TaskStatus.DONE
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    project_id: Optional[UUID] = Field(None, description="Updated project ID")
    scope_item_id: Optional[UUID] = Field(None, description="Updated scope item ID")
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated task title")
    due_date: Optional[date] = Field(None, description="Updated due date")
    status: Optional[TaskStatus] = Field(None, description="Updated status (To do, Doing, Done)")

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in ("to do", "todo"):
                return TaskStatus.TO_DO
            if clean in ("doing", "in_progress", "in progress"):
                return TaskStatus.DOING
            if clean == "done":
                return TaskStatus.DONE
        return v


class TaskRead(BaseModel):
    id: UUID
    workspace_id: UUID
    project_id: UUID
    scope_item_id: UUID
    title: str
    due_date: Optional[date] = None
    status: str
    project_name: Optional[str] = None
    scope_item_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
