import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Workspace(Base, TimestampMixin):
    """
    Agency Workspace tenant.
    Every agency has an isolated workspace to which all entities are bound.
    """
    __tablename__ = "workspaces"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    users = relationship("User", back_populates="workspace", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="workspace", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
    scope_items = relationship("ScopeItem", back_populates="workspace", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="workspace", cascade="all, delete-orphan")
    requests = relationship("Request", back_populates="workspace", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', slug='{self.slug}')>"
