"""Agent domain models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class AgentManifest(Base):
    """Agent manifest model - static agent definitions."""
    __tablename__ = "agent_manifests"
    
    agent_id = Column(String, primary_key=True)
    version = Column(String, primary_key=True)
    manifest = Column(JSONB, nullable=False)
    status = Column(String, default="active")  # active, deprecated, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # Note: One-way relationship - installations can reference manifest via composite key
    # installations = relationship("AgentInstallation", back_populates="manifest")
    
    __table_args__ = (
        Index("idx_agent_manifests_status", "status"),
    )


class AgentInstallation(Base):
    """Agent installation model - user-specific agent instances."""
    __tablename__ = "agent_installations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False)
    version = Column(String, nullable=False)
    status = Column(String, default="installed")  # installed, active, paused, uninstalled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="installations")
    manifest = relationship(
        "AgentManifest",
        primaryjoin="and_(AgentInstallation.agent_id == AgentManifest.agent_id, "
                    "AgentInstallation.version == AgentManifest.version)",
        foreign_keys=[agent_id, version],
        viewonly=True
    )
    context = relationship("AgentContext", back_populates="installation", uselist=False)
    
    __table_args__ = (
        Index("idx_agent_installations_user_status", "user_id", "status"),
        Index("idx_agent_installations_agent", "agent_id", "version"),
    )


class AgentContext(Base):
    """Agent context model - private memory for each agent installation."""
    __tablename__ = "agent_context"
    
    installation_id = Column(UUID(as_uuid=True), ForeignKey("agent_installations.id"), primary_key=True)
    agent_memory = Column(JSONB, nullable=False, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    installation = relationship("AgentInstallation", back_populates="context")
