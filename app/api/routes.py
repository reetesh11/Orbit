"""FastAPI routes."""
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.orchestrator import OrchestratorService
from app.cache import CacheService
from app.tools import ToolExecutor, ToolRegistry
from app.models import User, AgentManifest, AgentInstallation, Event, ToolExecution


router = APIRouter()


# Request/Response models
class InstallAgentRequest(BaseModel):
    agent_id: str
    version: str
    inputs: Dict[str, Any] = {}


class CreateEventRequest(BaseModel):
    event_type: str
    payload: Dict[str, Any]


class ApproveToolRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    comment: Optional[str] = None


# Dependencies
def get_tool_executor(
    request: Request,
    db: Session = Depends(get_db),
) -> ToolExecutor:
    """Get tool executor."""
    registry = getattr(request.app.state, "tool_registry", ToolRegistry())
    return ToolExecutor(db, registry)


def get_orchestrator(
    request: Request,
    db: Session = Depends(get_db),
    tool_executor: ToolExecutor = Depends(get_tool_executor),
) -> OrchestratorService:
    """Get orchestrator service."""
    cache = CacheService()
    orchestrator = OrchestratorService(db, cache, tool_executor)
    
    # Register agents from app state
    if hasattr(request.app.state, "agents"):
        for agent in request.app.state.agents.values():
            orchestrator.register_agent(agent)
    
    return orchestrator


# Routes
@router.get("/marketplace/agents")
def list_agents(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """List available agents in marketplace."""
    manifests = db.query(AgentManifest).filter_by(status="active").all()
    return [
        {
            "agent_id": m.agent_id,
            "version": m.version,
            "manifest": m.manifest,
        }
        for m in manifests
    ]


@router.get("/marketplace/agents/{agent_id}/{version}")
def get_agent(agent_id: str, version: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get agent manifest."""
    manifest = db.query(AgentManifest).filter_by(
        agent_id=agent_id,
        version=version,
        status="active",
    ).first()
    
    if not manifest:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": manifest.agent_id,
        "version": manifest.version,
        "manifest": manifest.manifest,
    }


@router.post("/users/{user_id}/agents/install")
def install_agent(
    user_id: uuid.UUID,
    request: InstallAgentRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Install an agent for a user."""
    try:
        installation = orchestrator.install_agent(
            user_id=user_id,
            agent_id=request.agent_id,
            version=request.version,
            inputs=request.inputs,
        )
        return {
            "installation_id": str(installation.id),
            "agent_id": installation.agent_id,
            "version": installation.version,
            "status": installation.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/agents")
def list_user_agents(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List user's installed agents."""
    installations = db.query(AgentInstallation).filter_by(
        user_id=user_id,
        status="active",
    ).all()
    
    return [
        {
            "installation_id": str(i.id),
            "agent_id": i.agent_id,
            "version": i.version,
            "status": i.status,
        }
        for i in installations
    ]


@router.post("/users/{user_id}/events")
def create_event(
    user_id: uuid.UUID,
    request: CreateEventRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """Create an event (user-initiated)."""
    try:
        event = orchestrator.process_event(
            user_id=user_id,
            event_type=request.event_type,
            payload=request.payload,
            source_agent=None,
        )
        return {
            "event_id": str(event.id),
            "event_type": event.event_type,
            "created_at": event.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/events")
def list_user_events(
    user_id: uuid.UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List user events."""
    events = db.query(Event).filter_by(
        user_id=user_id,
    ).order_by(Event.created_at.desc()).limit(limit).all()
    
    return [
        {
            "event_id": str(e.id),
            "event_type": e.event_type,
            "source_agent": e.source_agent,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/users/{user_id}/tools/pending")
def list_pending_tools(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """List pending tool executions requiring approval."""
    executions = db.query(ToolExecution).filter_by(
        user_id=user_id,
        status="pending",
    ).all()
    
    return [
        {
            "execution_id": str(e.id),
            "agent_id": e.agent_id,
            "tool_id": e.tool_id,
            "payload": e.payload,
            "created_at": e.created_at.isoformat(),
        }
        for e in executions
    ]


@router.post("/users/{user_id}/tools/{execution_id}/approve")
def approve_tool(
    user_id: uuid.UUID,
    execution_id: uuid.UUID,
    request: ApproveToolRequest,
    tool_executor: ToolExecutor = Depends(get_tool_executor),
) -> Dict[str, Any]:
    """Approve or reject a tool execution."""
    try:
        execution = tool_executor.approve_tool_execution(
            execution_id=execution_id,
            reviewer_id=user_id,
            decision=request.decision,
            comment=request.comment,
        )
        return {
            "execution_id": str(execution.id),
            "status": execution.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
