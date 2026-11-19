import uuid
from sqlalchemy import Column, Date, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Task(Base, TimestampMixin):
    """
    Actionable task derived from a scope item.
    Enforces that every task is strictly tied to a scope item and project within the workspace.
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
        ForeignKey("scope_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="To do")  # To do, Doing, Done

    # Relationships
    workspace = relationship("Workspace", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    scope_item = relationship("ScopeItem", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
