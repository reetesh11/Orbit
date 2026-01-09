"""Base agent interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.sdk.types import AgentManifest, AgentContext, AgentResult, Event


class BaseAgent(ABC):
    """Base agent interface.
    
    Agents are pure logic - no direct DB, network, or tool access.
    Deterministic execution with structured outputs only.
    """
    
    @abstractmethod
    def manifest(self) -> AgentManifest:
        """Return the agent manifest defining capabilities and permissions.
        
        Returns:
            AgentManifest: The agent's manifest
        """
        pass
    
    @abstractmethod
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Onboard the agent with user-specific inputs.
        
        This is called once during installation to personalize the agent.
        
        Args:
            inputs: User-provided inputs for personalization
            context: Initial context (user_profile, shared_context)
            
        Returns:
            dict: Initial agent_memory state
        """
        pass
    
    @abstractmethod
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle an event and return structured result.
        
        Args:
            event: The event to handle
            context: Full agent context (user_profile, shared_context, agent_memory, recent_events)
            
        Returns:
            AgentResult: Structured result with context updates, events, and tool executions
        """
        pass
