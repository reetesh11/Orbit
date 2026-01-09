"""Tool executor with human-in-the-loop support."""
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import ToolDefinition, ToolExecution, HumanApproval
from app.tools.registry import ToolRegistry


class ToolExecutor:
    """Tool executor service."""
    
    def __init__(self, db: Session, tool_registry: ToolRegistry):
        """Initialize tool executor.
        
        Args:
            db: Database session
            tool_registry: Tool registry
        """
        self.db = db
        self.tool_registry = tool_registry
    
    def execute_tool(
        self,
        user_id: uuid.UUID,
        agent_id: str,
        installation_id: Optional[uuid.UUID],
        tool_id: str,
        payload: Dict[str, Any],
    ) -> ToolExecution:
        """Execute a tool (with human approval if required).
        
        Args:
            user_id: User ID
            agent_id: Agent ID
            installation_id: Installation ID
            tool_id: Tool ID
            payload: Tool payload
            
        Returns:
            ToolExecution: Created execution record
        """
        # Get tool definition
        tool_def = self.db.query(ToolDefinition).filter_by(tool_id=tool_id).first()
        if not tool_def:
            raise ValueError(f"Tool {tool_id} not found")
        
        # Create execution record
        execution = ToolExecution(
            id=uuid.uuid4(),
            user_id=user_id,
            agent_id=agent_id,
            installation_id=installation_id,
            tool_id=tool_id,
            payload=payload,
            status="pending",
            created_at=datetime.utcnow(),
        )
        self.db.add(execution)
        self.db.flush()
        
        # Check if human approval is required
        requires_approval = tool_def.requires_human_approval == "true"
        
        if requires_approval:
            execution.status = "pending"
            # Wait for human approval
        else:
            # Execute immediately
            self._execute_tool_internal(execution, tool_def)
        
        self.db.commit()
        return execution
    
    def approve_tool_execution(
        self,
        execution_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        decision: str,
        comment: Optional[str] = None,
    ) -> ToolExecution:
        """Approve or reject a tool execution.
        
        Args:
            execution_id: Execution ID
            reviewer_id: Reviewer user ID
            decision: "approved" or "rejected"
            comment: Optional comment
            
        Returns:
            ToolExecution: Updated execution
        """
        execution = self.db.query(ToolExecution).filter_by(id=execution_id).first()
        if not execution:
            raise ValueError(f"Tool execution {execution_id} not found")
        
        if execution.status != "pending":
            raise ValueError(f"Tool execution {execution_id} is not pending approval")
        
        # Create approval record
        approval = HumanApproval(
            tool_execution_id=execution_id,
            reviewer_id=reviewer_id,
            decision=decision,
            comment=comment,
            created_at=datetime.utcnow(),
        )
        self.db.add(approval)
        
        if decision == "approved":
            execution.status = "approved"
            tool_def = self.db.query(ToolDefinition).filter_by(tool_id=execution.tool_id).first()
            if tool_def:
                self._execute_tool_internal(execution, tool_def)
        else:
            execution.status = "rejected"
        
        self.db.commit()
        return execution
    
    def _execute_tool_internal(self, execution: ToolExecution, tool_def: ToolDefinition):
        """Execute a tool internally.
        
        Args:
            execution: Tool execution record
            tool_def: Tool definition
        """
        try:
            execution.status = "executing"
            self.db.flush()
            
            # Get tool implementation from registry
            tool_impl = self.tool_registry.get_tool(execution.tool_id)
            if not tool_impl:
                raise ValueError(f"Tool implementation {execution.tool_id} not found")
            
            # Execute tool
            result = tool_impl.execute(execution.payload)
            
            execution.status = "completed"
            # Store result in payload or separate field if needed
            
        except Exception as e:
            execution.status = "failed"
            # Store error in execution record
            raise
