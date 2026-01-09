"""Tool and human-in-the-loop models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ToolDefinition(Base):
    """Tool definition model."""
    __tablename__ = "tool_definitions"
    
    tool_id = Column(String, primary_key=True)
    description = Column(Text, nullable=False)
    requires_human_approval = Column(String, default="false")  # true, false, optional
    approval_role = Column(String, nullable=True)  # admin, user, etc.
    risk_level = Column(String, default="low")  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    executions = relationship("ToolExecution", back_populates="tool_definition")


class ToolExecution(Base):
    """Tool execution model."""
    __tablename__ = "tool_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False)
    installation_id = Column(UUID(as_uuid=True), ForeignKey("agent_installations.id"), nullable=True)
    tool_id = Column(String, ForeignKey("tool_definitions.tool_id"), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String, default="pending")  # pending, approved, rejected, executing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tool_definition = relationship("ToolDefinition", back_populates="executions")
    approval = relationship("HumanApproval", back_populates="tool_execution", uselist=False)


class HumanApproval(Base):
    """Human approval model."""
    __tablename__ = "human_approvals"
    
    tool_execution_id = Column(UUID(as_uuid=True), ForeignKey("tool_executions.id"), primary_key=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(String, nullable=False)  # approved, rejected
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tool_execution = relationship("ToolExecution", back_populates="approval")
