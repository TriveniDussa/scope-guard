import uuid
from sqlalchemy import Column, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Request(Base, TimestampMixin):
    """
    Client Change Request entity.
    Submissions are evaluated by AI to detect scope creep against baseline scope_items.
    """
    __tablename__ = "requests"

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
    submitted_by_user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    ai_analysis = Column(Text, nullable=True)
    impact_hours = Column(Numeric(8, 2), nullable=True)
    impact_cost = Column(Numeric(12, 2), nullable=True)
    status = Column(
        String(50),
        nullable=False,
        default="pending_analysis",
    )  # pending_analysis, in_scope, scope_creep_detected, approved, rejected

    # Relationships
    workspace = relationship("Workspace", back_populates="requests")
    project = relationship("Project", back_populates="requests")
    submitted_by = relationship(
        "User",
        back_populates="submitted_requests",
        foreign_keys=[submitted_by_user_id],
    )

    def __repr__(self):
        return f"<Request(id={self.id}, title='{self.title}', status='{self.status}')>"
