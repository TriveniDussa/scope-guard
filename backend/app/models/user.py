import uuid
from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """
    User entity representing agency staff, admins, or client members.
    Strictly isolated within a specific workspace.
    """
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    workspace_id = Column(
        GUID,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="admin")
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="users")
    assigned_tasks = relationship(
        "Task",
        back_populates="assigned_to",
        foreign_keys="Task.assigned_to_user_id",
    )
    submitted_requests = relationship(
        "Request",
        back_populates="submitted_by",
        foreign_keys="Request.submitted_by_user_id",
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', workspace_id={self.workspace_id})>"
