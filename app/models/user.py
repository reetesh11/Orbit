"""User domain models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String, unique=True, nullable=True, index=True)
    email = Column(String, unique=True, nullable=True, index=True)
    status = Column(String, default="active")  # active, suspended, deleted
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    shared_context = relationship("SharedContext", back_populates="user", uselist=False)
    installations = relationship("AgentInstallation", back_populates="user")


class UserProfile(Base):
    """User profile model."""
    __tablename__ = "user_profile"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    profile = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="profile")


class SharedContext(Base):
    """Shared context model - collaborative writable surface for agents."""
    __tablename__ = "shared_context"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    context = Column(JSONB, nullable=False, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="shared_context")
