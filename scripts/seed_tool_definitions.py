"""Seed tool definitions."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import ToolDefinition


def seed_tool_definitions():
    """Seed tool definitions."""
    db = SessionLocal()
    
    try:
        tools = [
            {
                "tool_id": "create_meal_plan",
                "description": "Create a personalized meal plan",
                "requires_human_approval": "false",
                "approval_role": None,
                "risk_level": "low",
            },
            {
                "tool_id": "send_notification",
                "description": "Send a notification to the user",
                "requires_human_approval": "false",
                "approval_role": None,
                "risk_level": "low",
            },
        ]
        
        for tool_data in tools:
            existing = db.query(ToolDefinition).filter_by(
                tool_id=tool_data["tool_id"]
            ).first()
            
            if not existing:
                tool_def = ToolDefinition(**tool_data)
                db.add(tool_def)
        
        db.commit()
        print("Tool definitions seeded successfully")
    except Exception as e:
        db.rollback()
        print(f"Error seeding tool definitions: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_tool_definitions()
