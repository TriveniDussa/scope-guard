import uuid
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship, synonym

from app.core.database import Base, GUID
from app.models.base import TimestampMixin


class Client(Base, TimestampMixin):
    """
    Agency Client entity.
    Represents an external client organization that hires the agency.
    """
    __tablename__ = "clients"

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    workspace_id = Column(
        GUID,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    company_details = Column(Text, nullable=True)

    # Synonym allowing direct access via `client.email`
    email = synonym("contact_email")

    # Relationships
    workspace = relationship("Workspace", back_populates="clients")
    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', workspace_id={self.workspace_id})>"
