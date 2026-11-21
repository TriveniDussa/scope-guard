import uuid
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Request(Base, TimestampMixin):
    """
    Client Change Request evaluated by the AI Request Checker.
    Stores the client request text, the AI classification, explanation reason, and polite client reply.
    Supports user feedback ('Right'/'Wrong') and linked re-evaluations ('Check Again').
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
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_request_id = Column(
        GUID,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    client_request = Column(Text, nullable=False)
    classification = Column(String(50), nullable=False)  # "In scope", "Out of scope", "Not sure"
    reason = Column(Text, nullable=False)
    client_reply = Column(Text, nullable=False)
    feedback = Column(String(20), nullable=True)  # "Right", "Wrong"

    # Relationships
    workspace = relationship("Workspace", back_populates="requests")
    project = relationship("Project", back_populates="requests")
    user = relationship("User", back_populates="submitted_requests")
    lessons = relationship("Lesson", back_populates="request", cascade="all, delete-orphan")
    parent_request = relationship("Request", remote_side=[id], backref="re_evaluations")

    def __repr__(self):
        return f"<Request(id={self.id}, project_id={self.project_id}, classification='{self.classification}')>"
