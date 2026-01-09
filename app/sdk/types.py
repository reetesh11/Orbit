"""Agent SDK type definitions."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Event(BaseModel):
    """Event model for agent communication."""
    event_type: str
    source_agent: Optional[str] = None
    payload: Dict[str, Any]


class AgentManifest(BaseModel):
    """Agent manifest structure."""
    agent_id: str
    version: str
    name: str
    description: str
    
    # Input/output definitions
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Event subscriptions
    subscribed_events: List[str] = Field(default_factory=list)
    
    # Events this agent can emit
    emitted_events: List[str] = Field(default_factory=list)
    
    # Permissions
    permissions: Dict[str, Any] = Field(default_factory=dict)
    
    # Tools this agent can use
    tools: List[str] = Field(default_factory=list)
    
    # Collaboration rules
    collaboration_rules: Dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    """Agent context structure - what agents receive."""
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    agent_memory: Dict[str, Any] = Field(default_factory=dict)
    recent_events: List[Event] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Agent execution result."""
    # Context updates
    shared_context_updates: Dict[str, Any] = Field(default_factory=dict)
    agent_memory_updates: Dict[str, Any] = Field(default_factory=dict)
    
    # Events to emit
    events: List[Event] = Field(default_factory=list)
    
    # Tool executions to trigger
    tool_executions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Status
    status: str = "completed"  # completed, failed, pending_approval
    error: Optional[str] = None
