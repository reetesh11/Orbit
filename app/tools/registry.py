"""Tool registry for tool implementations."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Base tool interface."""
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool.
        
        Args:
            payload: Tool payload
            
        Returns:
            Execution result
        """
        pass


class ToolRegistry:
    """Registry for tool implementations."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool_id: str, tool: Tool):
        """Register a tool implementation.
        
        Args:
            tool_id: Tool ID
            tool: Tool implementation
        """
        self._tools[tool_id] = tool
    
    def get_tool(self, tool_id: str) -> Tool:
        """Get a tool implementation.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool implementation
        """
        return self._tools.get(tool_id)


# Example tool implementations
class CreateMealPlanTool(Tool):
    """Example tool for creating meal plans."""
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a meal plan."""
        target_weight = payload.get("target_weight")
        dietary_preferences = payload.get("dietary_preferences", [])
        
        # Mock implementation
        return {
            "status": "success",
            "meal_plan": {
                "breakfast": "Oatmeal with fruits",
                "lunch": "Grilled chicken salad",
                "dinner": "Salmon with vegetables",
            },
        }


class SendNotificationTool(Tool):
    """Example tool for sending notifications."""
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a notification."""
        message = payload.get("message", "")
        notification_type = payload.get("type", "info")
        
        # Mock implementation
        print(f"[{notification_type}] {message}")
        
        return {
            "status": "success",
            "sent_at": "2024-01-01T00:00:00Z",
        }
