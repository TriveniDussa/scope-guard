import uuid
from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class ScopeItem(Base, TimestampMixin):
    """
    Scope of Work (SOW) deliverable item.
    Establishes clear boundaries: what is explicitly included and what is excluded.
    """
    __tablename__ = "scope_items"

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
    included_description = Column(Text, nullable=False)
    not_included_description = Column(Text, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="scope_items")
    project = relationship("Project", back_populates="scope_items")
    tasks = relationship("Task", back_populates="scope_item")

    def __repr__(self):
        return f"<ScopeItem(id={self.id}, project_id={self.project_id})>"
