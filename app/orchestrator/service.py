"""Orchestrator service - handles agent installation and runtime execution."""
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import (
    User,
    AgentManifest,
    AgentInstallation,
    AgentContext,
    Event,
    ExecutionTrace,
)
from app.sdk.base import BaseAgent
from app.sdk.types import AgentContext as SDKAgentContext, Event as SDKEvent, AgentResult
from app.cache import CacheService


class OrchestratorService:
    """Orchestrator service for agent installation and execution."""
    
    def __init__(self, db: Session, cache: CacheService, tool_executor=None):
        """Initialize orchestrator.
        
        Args:
            db: Database session
            cache: Cache service for Redis
            tool_executor: Optional tool executor for processing tool executions
        """
        self.db = db
        self.cache = cache
        self.tool_executor = tool_executor
        self._agent_registry: Dict[str, BaseAgent] = {}
        self._max_event_hops = 10  # Prevent infinite loops
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent instance.
        
        Args:
            agent: Agent instance to register
        """
        manifest = agent.manifest()
        key = f"{manifest.agent_id}:{manifest.version}"
        self._agent_registry[key] = agent
    
    def install_agent(
        self,
        user_id: uuid.UUID,
        agent_id: str,
        version: str,
        inputs: Dict[str, Any],
    ) -> AgentInstallation:
        """Install an agent for a user (Section 9).
        
        Flow:
        1. Fetch agent_manifest
        2. Validate permissions & inputs
        3. Call agent.onboard()
        4. Persist agent_context
        5. Mark agent_installation active
        
        Args:
            user_id: User ID
            agent_id: Agent ID
            version: Agent version
            inputs: User-provided inputs for onboarding
            
        Returns:
            AgentInstallation: Created installation
        """
        # Fetch manifest
        manifest = self.db.query(AgentManifest).filter_by(
            agent_id=agent_id,
            version=version,
            status="active"
        ).first()
        
        if not manifest:
            raise ValueError(f"Agent {agent_id}:{version} not found or not active")
        
        # Check if already installed
        existing = self.db.query(AgentInstallation).filter_by(
            user_id=user_id,
            agent_id=agent_id,
            version=version,
        ).first()
        
        if existing:
            raise ValueError(f"Agent {agent_id}:{version} already installed for user")
        
        # Get agent instance
        agent_key = f"{agent_id}:{version}"
        agent = self._agent_registry.get(agent_key)
        if not agent:
            raise ValueError(f"Agent {agent_id}:{version} not registered")
        
        # Build initial context
        user = self.db.query(User).filter_by(id=user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        

        # Create installation
        installation = AgentInstallation(
            id=uuid.uuid4(),
            user_id=user_id,
            agent_id=agent_id,
            version=version,
            status="active",
        )
        self.db.add(installation)
        self.db.flush()

        user_profile = user.profile.profile if user.profile else {}
        shared_context = user.shared_context.context if user.shared_context else {}
        
        initial_context = SDKAgentContext(
            user_profile=user_profile,
            shared_context=shared_context,
            agent_memory={},
            recent_events=[],
        )
        
        # Call agent.onboard()
        agent_memory = agent.onboard(inputs, initial_context)
        
        # Create agent context
        agent_context = AgentContext(
            installation_id=installation.id,
            agent_memory=agent_memory,
        )
        self.db.add(agent_context)
        self.db.commit()
        
        # Invalidate cache
        self.cache.invalidate_user_installations(user_id)
        
        return installation
    
    def process_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        payload: Dict[str, Any],
        source_agent: Optional[str] = None,
        event_hop: int = 0,
    ) -> Event:
        """Process an event and trigger agent execution (Section 10).
        
        Flow:
        1. Persist event
        2. Find subscribed agents
        3. Load scoped context
        4. Execute agent.handle_event()
        5. Validate output
        6. Apply context updates
        7. Create tool executions
        8. Emit new events
        
        Args:
            user_id: User ID
            event_type: Event type
            payload: Event payload
            source_agent: Source agent (None for user-initiated)
            event_hop: Current hop count (for loop prevention)
            
        Returns:
            Event: Created event
        """
        # Guardrails: prevent infinite loops
        if event_hop >= self._max_event_hops:
            raise ValueError(f"Max event hops ({self._max_event_hops}) reached")
        
        # Persist event
        event = Event(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type=event_type,
            source_agent=source_agent,
            payload=payload,
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        self.db.flush()
        
        # Find subscribed agents
        installations = self._get_subscribed_installations(user_id, event_type)
        
        # Execute each subscribed agent
        new_events: List[Dict[str, Any]] = []
        
        for installation in installations:
            # Prevent self-loops
            if source_agent == installation.agent_id:
                continue
            
            try:
                result = self._execute_agent(installation, event)
                
                # Apply context updates
                self._apply_context_updates(installation, result)
                
                # Create tool executions (handled by ToolExecutor)
                if self.tool_executor and result.tool_executions:
                    for tool_exec in result.tool_executions:
                        try:
                            self.tool_executor.execute_tool(
                                user_id=user_id,
                                agent_id=installation.agent_id,
                                installation_id=installation.id,
                                tool_id=tool_exec["tool_id"],
                                payload=tool_exec["payload"],
                            )
                        except Exception as e:
                            # Log but don't fail entire pipeline
                            print(f"Error executing tool {tool_exec.get('tool_id')}: {e}")
                
                # Collect new events
                for new_event in result.events:
                    new_events.append({
                        "event_type": new_event.event_type,
                        "payload": new_event.payload,
                        "source_agent": installation.agent_id,
                    })
                    
            except Exception as e:
                # Log error but continue processing other agents
                trace = ExecutionTrace(
                    id=uuid.uuid4(),
                    event_id=event.id,
                    agent_id=installation.agent_id,
                    installation_id=installation.id,
                    status="failed",
                    error=str(e),
                    started_at=datetime.utcnow(),
                    finished_at=datetime.utcnow(),
                )
                self.db.add(trace)
                continue
        
        self.db.commit()
        
        # Process new events recursively (controlled DAG)
        for new_event_data in new_events:
            try:
                self.process_event(
                    user_id=user_id,
                    event_type=new_event_data["event_type"],
                    payload=new_event_data["payload"],
                    source_agent=new_event_data["source_agent"],
                    event_hop=event_hop + 1,
                )
            except Exception as e:
                # Log but don't fail entire pipeline
                print(f"Error processing cascading event: {e}")
        
        return event
    
    def _get_subscribed_installations(
        self,
        user_id: uuid.UUID,
        event_type: str,
    ) -> List[AgentInstallation]:
        """Get active installations subscribed to an event type.
        
        Args:
            user_id: User ID
            event_type: Event type
            
        Returns:
            List of subscribed installations
        """
        # Get cached installations
        installations = self.cache.get_user_installations(user_id)
        
        if not installations:
            # Query from DB
            installations = self.db.query(AgentInstallation).filter_by(
                user_id=user_id,
                status="active",
            ).all()
            
            # Cache them
            self.cache.set_user_installations(user_id, installations)
        
        # Filter by subscribed events
        subscribed = []
        for installation in installations:
            # Get manifest
            manifest = self.cache.get_agent_manifest(installation.agent_id, installation.version)
            if not manifest:
                manifest_obj = self.db.query(AgentManifest).filter_by(
                    agent_id=installation.agent_id,
                    version=installation.version,
                ).first()
                if manifest_obj:
                    manifest = manifest_obj.manifest
                    self.cache.set_agent_manifest(installation.agent_id, installation.version, manifest)
            
            if manifest and event_type in manifest.get("subscribed_events", []):
                subscribed.append(installation)
        
        return subscribed
    
    def _execute_agent(
        self,
        installation: AgentInstallation,
        event: Event,
    ) -> AgentResult:
        """Execute an agent's handle_event method.
        
        Args:
            installation: Agent installation
            event: Event to handle
            
        Returns:
            AgentResult: Agent execution result
        """
        # Get agent instance
        agent_key = f"{installation.agent_id}:{installation.version}"
        agent = self._agent_registry.get(agent_key)
        if not agent:
            raise ValueError(f"Agent {agent_key} not registered")
        
        # Create execution trace
        trace = ExecutionTrace(
            id=uuid.uuid4(),
            event_id=event.id,
            agent_id=installation.agent_id,
            installation_id=installation.id,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(trace)
        self.db.flush()
        
        try:
            # Load context
            context = self._build_agent_context(installation, event)
            
            # Build SDK event
            sdk_event = SDKEvent(
                event_type=event.event_type,
                source_agent=event.source_agent,
                payload=event.payload,
            )
            
            # Execute agent
            result = agent.handle_event(sdk_event, context)
            
            # Update trace
            trace.status = "completed"
            trace.finished_at = datetime.utcnow()
            
            return result
            
        except Exception as e:
            trace.status = "failed"
            trace.error = str(e)
            trace.finished_at = datetime.utcnow()
            raise
    
    def _build_agent_context(
        self,
        installation: AgentInstallation,
        event: Event,
    ) -> SDKAgentContext:
        """Build agent context from database.
        
        Args:
            installation: Agent installation
            event: Current event
            
        Returns:
            SDKAgentContext: Built context
        """
        # Get user data
        user = installation.user
        user_profile = user.profile.profile if user.profile else {}
        shared_context = user.shared_context.context if user.shared_context else {}
        
        # Get agent memory
        agent_context = installation.context
        agent_memory = agent_context.agent_memory if agent_context else {}
        
        # Get recent events (last 10)
        recent_events = self.db.query(Event).filter_by(
            user_id=installation.user_id,
        ).order_by(Event.created_at.desc()).limit(10).all()
        
        recent_sdk_events = [
            SDKEvent(
                event_type=e.event_type,
                source_agent=e.source_agent,
                payload=e.payload,
            )
            for e in recent_events
        ]
        
        return SDKAgentContext(
            user_profile=user_profile,
            shared_context=shared_context,
            agent_memory=agent_memory,
            recent_events=recent_sdk_events,
        )
    
    def _apply_context_updates(
        self,
        installation: AgentInstallation,
        result: AgentResult,
    ):
        """Apply context updates from agent result.
        
        Args:
            installation: Agent installation
            result: Agent result with updates
        """
        # Update shared context (if agent has permission)
        if result.shared_context_updates:
            user = installation.user
            if not user.shared_context:
                from app.models import SharedContext
                user.shared_context = SharedContext(
                    user_id=user.id,
                    context=result.shared_context_updates,
                )
                self.db.add(user.shared_context)
            else:
                # Merge updates
                current = user.shared_context.context or {}
                current.update(result.shared_context_updates)
                user.shared_context.context = current
        
        # Update agent memory
        if result.agent_memory_updates:
            agent_context = installation.context
            if not agent_context:
                agent_context = AgentContext(
                    installation_id=installation.id,
                    agent_memory=result.agent_memory_updates,
                )
                self.db.add(agent_context)
            else:
                # Merge updates
                current = agent_context.agent_memory or {}
                current.update(result.agent_memory_updates)
                agent_context.agent_memory = current
