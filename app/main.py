"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.sdk.examples import (
    HealthGoalAgent,
    CookingAgent,
    ReminderAgent,
    TaxFilingAgent,
    InvoiceAgent,
    ResumeShortlisterAgent,
    OnboardingAgent,
    FitnessCoachAgent,
    BudgetTrackerAgent,
    TeamCoordinatorAgent,
    CommutePlannerAgent,
    EmailOrganizerAgent,
    CalendarAgent,
    ExpenseTrackerAgent,
    TaskManagerAgent,
    LearningAssistantAgent,
    WeatherAgent,
    ShoppingAssistantAgent,
    NewsAggregatorAgent,
)
from app.tools.registry import ToolRegistry, CreateMealPlanTool, SendNotificationTool
from app.database import engine, Base
from app.models import *  # noqa: F401, F403
from app.config import settings


# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Agent Marketplace Platform",
    description="Platform for installing, personalizing, and orchestrating AI agents",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["api"])


def initialize_agents():
    """Initialize and register all available agents."""
    return {
        "health_goal_agent:1.0.0": HealthGoalAgent(),
        "cooking_agent:1.0.0": CookingAgent(),
        "reminder_agent:1.0.0": ReminderAgent(),
        "tax_filing_agent:1.0.0": TaxFilingAgent(),
        "invoice_agent:1.0.0": InvoiceAgent(),
        "resume_shortlister_agent:1.0.0": ResumeShortlisterAgent(),
        "onboarding_agent:1.0.0": OnboardingAgent(),
        "fitness_coach_agent:1.0.0": FitnessCoachAgent(),
        "budget_tracker_agent:1.0.0": BudgetTrackerAgent(),
        "team_coordinator_agent:1.0.0": TeamCoordinatorAgent(),
        "commute_planner_agent:1.0.0": CommutePlannerAgent(),
        "email_organizer_agent:1.0.0": EmailOrganizerAgent(),
        "calendar_agent:1.0.0": CalendarAgent(),
        "expense_tracker_agent:1.0.0": ExpenseTrackerAgent(),
        "task_manager_agent:1.0.0": TaskManagerAgent(),
        "learning_assistant_agent:1.0.0": LearningAssistantAgent(),
        "weather_agent:1.0.0": WeatherAgent(),
        "shopping_assistant_agent:1.0.0": ShoppingAssistantAgent(),
        "news_aggregator_agent:1.0.0": NewsAggregatorAgent(),
    }


def initialize_tools():
    """Initialize and register all available tools."""
    tool_registry = ToolRegistry()
    tool_registry.register_tool("create_meal_plan", CreateMealPlanTool())
    tool_registry.register_tool("send_notification", SendNotificationTool())
    return tool_registry


def seed_agent_manifests(agents):
    """Seed agent manifests in the database if they don't exist."""
    from app.database import SessionLocal
    from app.models import AgentManifest
    
    db = SessionLocal()
    try:
        for agent in agents.values():
            manifest = agent.manifest()
            existing = db.query(AgentManifest).filter_by(
                agent_id=manifest.agent_id,
                version=manifest.version,
            ).first()
            
            if not existing:
                agent_manifest = AgentManifest(
                    agent_id=manifest.agent_id,
                    version=manifest.version,
                    manifest=manifest.model_dump(),
                    status="active",
                )
                db.add(agent_manifest)
        
        db.commit()
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """Initialize agents and tools on startup."""
    # Initialize agents
    agents = initialize_agents()
    app.state.agents = agents
    
    # Initialize tools
    tool_registry = initialize_tools()
    app.state.tool_registry = tool_registry
    
    # Seed agent manifests
    seed_agent_manifests(agents)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Orbit: Agent Marketplace Platform API",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}
