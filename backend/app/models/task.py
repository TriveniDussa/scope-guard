import uuid
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Task(Base, TimestampMixin):
    """
    Actionable task derived from a scope item or project milestones.
    """
    __tablename__ = "tasks"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    workspace_id = Column(
        GUID,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        GUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_item_id = Column(
        GUID,
        ForeignKey("scope_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to_user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="todo")  # todo, in_progress, in_review, done
    priority = Column(String(50), nullable=False, default="medium")  # low, medium, high, urgent
    due_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    scope_item = relationship("ScopeItem", back_populates="tasks")
    assigned_to = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assigned_to_user_id],
    )

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
