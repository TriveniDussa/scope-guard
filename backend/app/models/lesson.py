import uuid
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Lesson(Base, TimestampMixin):
    """
    Retrospective Agency Correction Lesson Learned entity.
    Stores human corrections to AI classifications on client requests for a specific project.
    Used by the AI Request Checker as prompt guidance to improve future and re-evaluated predictions.
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
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    request_id = Column(
        GUID,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ai_answer = Column(String(50), nullable=False)
    correct_result = Column(String(50), nullable=False)  # "In scope" or "Out of scope"
    correction_reason = Column(Text, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="lessons")
    project = relationship("Project", back_populates="lessons")
    request = relationship("Request", back_populates="lessons")

    def __repr__(self):
        return (
            f"<Lesson(id={self.id}, project_id={self.project_id}, "
            f"ai_answer='{self.ai_answer}', correct_result='{self.correct_result}')>"
        )
