"""Event and execution trace models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Event(Base):
    """Event model - immutable, append-only events."""
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    source_agent = Column(String, nullable=True)  # null for user-initiated events
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    execution_traces = relationship("ExecutionTrace", back_populates="event")
    
    __table_args__ = (
        Index("idx_events_user_created", "user_id", "created_at"),
    )


class ExecutionTrace(Base):
    """Execution trace model - observability and debugging."""
    __tablename__ = "execution_traces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    agent_id = Column(String, nullable=False)
    installation_id = Column(UUID(as_uuid=True), ForeignKey("agent_installations.id"), nullable=True)
    status = Column(String, nullable=False)  # pending, running, completed, failed
    error = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="execution_traces")
    
    __table_args__ = (
        Index("idx_execution_traces_event", "event_id"),
        Index("idx_execution_traces_agent", "agent_id"),
    )
