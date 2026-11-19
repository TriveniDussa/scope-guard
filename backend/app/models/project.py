import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Project(Base, TimestampMixin):
    """
    Project / Statement of Work engagement entity.
    Scoped to both a workspace and an agency client.
    """
    __tablename__ = "projects"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    workspace_id = Column(
        GUID,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_id = Column(
        GUID,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    budget = Column(Numeric(12, 2), nullable=True)
    status = Column(String(50), nullable=False, default="Active")  # Active, Done
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    scope_items = relationship("ScopeItem", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    requests = relationship("Request", back_populates="project", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', client_id={self.client_id})>"
