import uuid
from sqlalchemy import Column, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class ScopeItem(Base, TimestampMixin):
    """
    Scope of Work (SOW) deliverable item.
    Acts as the baseline truth of what was contracted and agreed upon.
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
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="included")  # included, out_of_scope, pending_approval
    estimated_hours = Column(Numeric(8, 2), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="scope_items")
    project = relationship("Project", back_populates="scope_items")
    tasks = relationship("Task", back_populates="scope_item")

    def __repr__(self):
        return f"<ScopeItem(id={self.id}, title='{self.title}', project_id={self.project_id})>"
