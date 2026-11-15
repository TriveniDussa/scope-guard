import uuid
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Lesson(Base, TimestampMixin):
    """
    Retrospective Lesson Learned entity.
    Captures scope insights, estimation variances, and risk mitigations for the agency.
    """
    __tablename__ = "lessons"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    workspace_id = Column(
        GUID,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        GUID,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(255), nullable=False)
    category = Column(
        String(100),
        nullable=False,
        default="general",
    )  # estimation, client_communication, technical_debt, contract_terms
    content = Column(Text, nullable=False)
    action_items = Column(Text, nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="lessons")
    project = relationship("Project", back_populates="lessons")

    def __repr__(self):
        return f"<Lesson(id={self.id}, title='{self.title}', category='{self.category}')>"
