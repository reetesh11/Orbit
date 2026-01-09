"""Example agents for MVP."""
from typing import Any, Dict

from app.sdk.base import BaseAgent
from app.sdk.types import AgentManifest, AgentContext, AgentResult, Event


class HealthGoalAgent(BaseAgent):
    """Example agent for managing health goals."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="health_goal_agent",
            version="1.0.0",
            name="Health Agent",
            description="Manages your diet, workout schedules, and wellness goals while coordinating with other agents.",
            inputs={
                "target_weight": {"type": "number", "required": False},
                "dietary_preferences": {"type": "array", "required": False},
            },
            outputs={},
            subscribed_events=[],
            emitted_events=["health_goal_updated"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=[],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory with user inputs."""
        return {
            "target_weight": inputs.get("target_weight"),
            "dietary_preferences": inputs.get("dietary_preferences", []),
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle events (none subscribed in MVP)."""
        return AgentResult()


class CookingAgent(BaseAgent):
    """Example agent for meal planning."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="cooking_agent",
            version="1.0.0",
            name="Cooking Agent",
            description="Plans your meals, creates shopping lists, and adapts to your dietary preferences and what's in your fridge.",
            inputs={},
            outputs={},
            subscribed_events=["health_goal_updated"],
            emitted_events=["meal_plan_created"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["create_meal_plan"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "preferences": {},
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle health goal updates and create meal plans."""
        if event.event_type == "health_goal_updated":
            # Read health goals from shared context
            health_goals = context.shared_context.get("health_goals", {})
            
            # Create meal plan tool execution
            tool_execution = {
                "tool_id": "create_meal_plan",
                "payload": {
                    "target_weight": health_goals.get("target_weight"),
                    "dietary_preferences": health_goals.get("dietary_preferences", []),
                },
            }
            
            # Emit meal plan created event (will be emitted after tool execution)
            result_event = Event(
                event_type="meal_plan_created",
                source_agent="cooking_agent",
                payload={"status": "pending"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class ReminderAgent(BaseAgent):
    """Example agent for sending reminders."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="reminder_agent",
            version="1.0.0",
            name="Reminder Agent",
            description="Smart notifications that sync with all your agents to keep you on track throughout the day.",
            inputs={},
            outputs={},
            subscribed_events=["meal_plan_created"],
            emitted_events=["reminder_sent"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": False,
            },
            tools=["send_notification"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "reminder_preferences": {"enabled": True},
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle meal plan creation and send reminders."""
        if event.event_type == "meal_plan_created":
            tool_execution = {
                "tool_id": "send_notification",
                "payload": {
                    "message": "Your meal plan has been created! Check it out.",
                    "type": "reminder",
                },
            }
            
            result_event = Event(
                event_type="reminder_sent",
                source_agent="reminder_agent",
                payload={"status": "sent"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


# Agents from screenshot
class TaxFilingAgent(BaseAgent):
    """Agent for organizing documents, tracking deductions, and preparing for tax season."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="tax_filing_agent",
            version="1.0.0",
            name="Tax Filing Agent",
            description="Helps you organize documents, track deductions, and prepare for tax season with ease.",
            inputs={
                "tax_year": {"type": "number", "required": False},
                "filing_status": {"type": "string", "required": False},
            },
            outputs={},
            subscribed_events=["expense_tracked", "invoice_created"],
            emitted_events=["tax_document_organized", "deduction_tracked"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["organize_documents", "calculate_deductions"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "tax_year": inputs.get("tax_year", 2024),
            "filing_status": inputs.get("filing_status", "single"),
            "documents": [],
            "deductions": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle expense and invoice events to track tax-related information."""
        if event.event_type in ["expense_tracked", "invoice_created"]:
            tool_execution = {
                "tool_id": "organize_documents",
                "payload": {
                    "event_type": event.event_type,
                    "data": event.payload,
                },
            }
            
            result_event = Event(
                event_type="tax_document_organized",
                source_agent="tax_filing_agent",
                payload={"status": "processed"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class InvoiceAgent(BaseAgent):
    """Agent for creating professional invoices, tracking payments, and managing billing workflow."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="invoice_agent",
            version="1.0.0",
            name="Invoice Agent",
            description="Creates professional invoices, tracks payments, and manages your billing workflow.",
            inputs={
                "business_name": {"type": "string", "required": False},
                "currency": {"type": "string", "required": False},
            },
            outputs={},
            subscribed_events=[],
            emitted_events=["invoice_created", "payment_received"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["create_invoice", "track_payment"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "business_name": inputs.get("business_name", ""),
            "currency": inputs.get("currency", "USD"),
            "invoices": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle invoice-related events."""
        return AgentResult()


class ResumeShortlisterAgent(BaseAgent):
    """Agent for analyzing candidates against job descriptions and ranking them by fit."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="resume_shortlister_agent",
            version="1.0.0",
            name="Resume Shortlister",
            description="Analyzes candidates against job descriptions and ranks them by fit for your roles.",
            inputs={
                "job_description": {"type": "string", "required": False},
                "ranking_criteria": {"type": "array", "required": False},
            },
            outputs={},
            subscribed_events=["resume_received"],
            emitted_events=["candidate_ranked", "shortlist_updated"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["analyze_resume", "rank_candidates"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "job_description": inputs.get("job_description", ""),
            "ranking_criteria": inputs.get("ranking_criteria", []),
            "candidates": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle resume received events."""
        if event.event_type == "resume_received":
            tool_execution = {
                "tool_id": "analyze_resume",
                "payload": {
                    "resume_data": event.payload,
                    "job_description": context.agent_memory.get("job_description"),
                },
            }
            
            result_event = Event(
                event_type="candidate_ranked",
                source_agent="resume_shortlister_agent",
                payload={"status": "analyzed"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class OnboardingAgent(BaseAgent):
    """Agent for guiding new hires through company processes and answering questions."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="onboarding_agent",
            version="1.0.0",
            name="Onboarding Agent",
            description="Guides new hires through company processes and answers their questions in real-time.",
            inputs={
                "company_policies": {"type": "array", "required": False},
                "onboarding_checklist": {"type": "array", "required": False},
            },
            outputs={},
            subscribed_events=["new_hire_question"],
            emitted_events=["onboarding_step_completed", "question_answered"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["answer_question", "update_checklist"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "company_policies": inputs.get("company_policies", []),
            "onboarding_checklist": inputs.get("onboarding_checklist", []),
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle new hire questions."""
        if event.event_type == "new_hire_question":
            tool_execution = {
                "tool_id": "answer_question",
                "payload": {
                    "question": event.payload.get("question"),
                    "context": context.agent_memory.get("company_policies", []),
                },
            }
            
            result_event = Event(
                event_type="question_answered",
                source_agent="onboarding_agent",
                payload={"status": "answered"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class FitnessCoachAgent(BaseAgent):
    """Agent for creating personalized workout plans and tracking fitness progress."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="fitness_coach_agent",
            version="1.0.0",
            name="Fitness Coach",
            description="Creates personalized workout plans and tracks your progress towards fitness goals.",
            inputs={
                "fitness_level": {"type": "string", "required": False},
                "goal_type": {"type": "string", "required": False},
                "available_time": {"type": "number", "required": False},
            },
            outputs={},
            subscribed_events=["health_goal_updated"],
            emitted_events=["workout_plan_created", "progress_tracked"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["create_workout_plan", "track_progress"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "fitness_level": inputs.get("fitness_level", "beginner"),
            "goal_type": inputs.get("goal_type", "general"),
            "available_time": inputs.get("available_time", 30),
            "workout_history": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle health goal updates."""
        if event.event_type == "health_goal_updated":
            tool_execution = {
                "tool_id": "create_workout_plan",
                "payload": {
                    "health_goals": event.payload,
                    "fitness_level": context.agent_memory.get("fitness_level"),
                    "available_time": context.agent_memory.get("available_time"),
                },
            }
            
            result_event = Event(
                event_type="workout_plan_created",
                source_agent="fitness_coach_agent",
                payload={"status": "created"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class BudgetTrackerAgent(BaseAgent):
    """Agent for monitoring spending, setting savings goals, and providing financial insights."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="budget_tracker_agent",
            version="1.0.0",
            name="Budget Tracker",
            description="Monitors spending, sets savings goals, and provides insights on your financial health.",
            inputs={
                "monthly_income": {"type": "number", "required": False},
                "savings_goal": {"type": "number", "required": False},
            },
            outputs={},
            subscribed_events=["expense_tracked", "income_received"],
            emitted_events=["budget_alert", "savings_goal_met"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["analyze_spending", "generate_insights"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "monthly_income": inputs.get("monthly_income", 0),
            "savings_goal": inputs.get("savings_goal", 0),
            "expenses": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle expense and income tracking."""
        if event.event_type in ["expense_tracked", "income_received"]:
            tool_execution = {
                "tool_id": "analyze_spending",
                "payload": {
                    "event_type": event.event_type,
                    "data": event.payload,
                    "monthly_income": context.agent_memory.get("monthly_income"),
                    "savings_goal": context.agent_memory.get("savings_goal"),
                },
            }
            
            result_event = Event(
                event_type="budget_alert",
                source_agent="budget_tracker_agent",
                payload={"status": "analyzed"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class TeamCoordinatorAgent(BaseAgent):
    """Agent for scheduling meetings, managing team tasks, and keeping everyone aligned."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="team_coordinator_agent",
            version="1.0.0",
            name="Team Coordinator",
            description="Schedules meetings, manages team tasks, and keeps everyone aligned on projects.",
            inputs={
                "team_members": {"type": "array", "required": False},
                "working_hours": {"type": "object", "required": False},
            },
            outputs={},
            subscribed_events=["meeting_requested", "task_created"],
            emitted_events=["meeting_scheduled", "task_assigned"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["schedule_meeting", "assign_task"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "team_members": inputs.get("team_members", []),
            "working_hours": inputs.get("working_hours", {}),
            "meetings": [],
            "tasks": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle meeting requests and task creation."""
        if event.event_type == "meeting_requested":
            tool_execution = {
                "tool_id": "schedule_meeting",
                "payload": {
                    "meeting_details": event.payload,
                    "team_members": context.agent_memory.get("team_members"),
                    "working_hours": context.agent_memory.get("working_hours"),
                },
            }
            
            result_event = Event(
                event_type="meeting_scheduled",
                source_agent="team_coordinator_agent",
                payload={"status": "scheduled"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        elif event.event_type == "task_created":
            tool_execution = {
                "tool_id": "assign_task",
                "payload": {
                    "task": event.payload,
                    "team_members": context.agent_memory.get("team_members"),
                },
            }
            
            result_event = Event(
                event_type="task_assigned",
                source_agent="team_coordinator_agent",
                payload={"status": "assigned"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class CommutePlannerAgent(BaseAgent):
    """Agent for optimizing daily travel, suggesting routes, and coordinating with schedule."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="commute_planner_agent",
            version="1.0.0",
            name="Commute Planner",
            description="Optimizes your daily travel, suggests best routes, and coordinates with your schedule.",
            inputs={
                "home_address": {"type": "string", "required": False},
                "work_address": {"type": "string", "required": False},
                "preferred_transport": {"type": "array", "required": False},
            },
            outputs={},
            subscribed_events=["meeting_scheduled", "calendar_updated"],
            emitted_events=["route_optimized", "commute_alert"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["optimize_route", "check_traffic"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "home_address": inputs.get("home_address", ""),
            "work_address": inputs.get("work_address", ""),
            "preferred_transport": inputs.get("preferred_transport", ["car"]),
            "routes": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle schedule changes."""
        if event.event_type in ["meeting_scheduled", "calendar_updated"]:
            tool_execution = {
                "tool_id": "optimize_route",
                "payload": {
                    "destination": event.payload.get("location"),
                    "preferred_transport": context.agent_memory.get("preferred_transport"),
                },
            }
            
            result_event = Event(
                event_type="route_optimized",
                source_agent="commute_planner_agent",
                payload={"status": "optimized"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


# Additional day-to-day agents
class EmailOrganizerAgent(BaseAgent):
    """Agent for organizing emails, prioritizing important messages, and managing inbox."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="email_organizer_agent",
            version="1.0.0",
            name="Email Organizer",
            description="Organizes your emails, prioritizes important messages, and helps manage your inbox efficiently.",
            inputs={
                "email_provider": {"type": "string", "required": False},
                "priority_keywords": {"type": "array", "required": False},
            },
            outputs={},
            subscribed_events=["email_received"],
            emitted_events=["email_categorized", "important_email_alert"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["categorize_email", "prioritize_message"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "email_provider": inputs.get("email_provider", ""),
            "priority_keywords": inputs.get("priority_keywords", []),
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle incoming emails."""
        if event.event_type == "email_received":
            tool_execution = {
                "tool_id": "categorize_email",
                "payload": {
                    "email": event.payload,
                    "priority_keywords": context.agent_memory.get("priority_keywords"),
                },
            }
            
            result_event = Event(
                event_type="email_categorized",
                source_agent="email_organizer_agent",
                payload={"status": "categorized"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class CalendarAgent(BaseAgent):
    """Agent for managing calendar events, scheduling, and providing reminders."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="calendar_agent",
            version="1.0.0",
            name="Calendar Agent",
            description="Manages your calendar events, optimizes scheduling, and sends timely reminders.",
            inputs={
                "calendar_provider": {"type": "string", "required": False},
                "reminder_preferences": {"type": "object", "required": False},
            },
            outputs={},
            subscribed_events=["meeting_requested", "task_created"],
            emitted_events=["calendar_updated", "reminder_sent"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["create_event", "send_reminder"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "calendar_provider": inputs.get("calendar_provider", ""),
            "reminder_preferences": inputs.get("reminder_preferences", {}),
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle meeting and task events."""
        if event.event_type == "meeting_requested":
            tool_execution = {
                "tool_id": "create_event",
                "payload": {
                    "meeting": event.payload,
                },
            }
            
            result_event = Event(
                event_type="calendar_updated",
                source_agent="calendar_agent",
                payload={"status": "event_created"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class ExpenseTrackerAgent(BaseAgent):
    """Agent for tracking expenses, categorizing spending, and generating expense reports."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="expense_tracker_agent",
            version="1.0.0",
            name="Expense Tracker",
            description="Tracks your expenses, categorizes spending automatically, and generates detailed expense reports.",
            inputs={
                "categories": {"type": "array", "required": False},
                "auto_categorize": {"type": "boolean", "required": False},
            },
            outputs={},
            subscribed_events=["transaction_occurred"],
            emitted_events=["expense_tracked", "report_generated"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["categorize_expense", "generate_report"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "categories": inputs.get("categories", []),
            "auto_categorize": inputs.get("auto_categorize", True),
            "expenses": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle transaction events."""
        if event.event_type == "transaction_occurred":
            tool_execution = {
                "tool_id": "categorize_expense",
                "payload": {
                    "transaction": event.payload,
                    "categories": context.agent_memory.get("categories"),
                },
            }
            
            result_event = Event(
                event_type="expense_tracked",
                source_agent="expense_tracker_agent",
                payload={"status": "tracked"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class TaskManagerAgent(BaseAgent):
    """Agent for managing tasks, setting priorities, and tracking progress."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="task_manager_agent",
            version="1.0.0",
            name="Task Manager",
            description="Manages your tasks, sets priorities, tracks progress, and suggests optimal work schedules.",
            inputs={
                "productivity_style": {"type": "string", "required": False},
                "priority_method": {"type": "string", "required": False},
            },
            outputs={},
            subscribed_events=["task_created", "deadline_approaching"],
            emitted_events=["task_prioritized", "task_completed", "deadline_alert"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["prioritize_task", "schedule_work"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "productivity_style": inputs.get("productivity_style", "balanced"),
            "priority_method": inputs.get("priority_method", "urgency"),
            "tasks": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle task-related events."""
        if event.event_type == "task_created":
            tool_execution = {
                "tool_id": "prioritize_task",
                "payload": {
                    "task": event.payload,
                    "priority_method": context.agent_memory.get("priority_method"),
                },
            }
            
            result_event = Event(
                event_type="task_prioritized",
                source_agent="task_manager_agent",
                payload={"status": "prioritized"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class LearningAssistantAgent(BaseAgent):
    """Agent for managing learning goals, tracking progress, and suggesting resources."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="learning_assistant_agent",
            version="1.0.0",
            name="Learning Assistant",
            description="Manages your learning goals, tracks progress, suggests resources, and schedules study time.",
            inputs={
                "learning_goals": {"type": "array", "required": False},
                "preferred_format": {"type": "array", "required": False},
            },
            outputs={},
            subscribed_events=["learning_goal_set"],
            emitted_events=["study_plan_created", "progress_updated"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["create_study_plan", "suggest_resources"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "learning_goals": inputs.get("learning_goals", []),
            "preferred_format": inputs.get("preferred_format", ["video", "article"]),
            "progress": {},
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle learning goal events."""
        if event.event_type == "learning_goal_set":
            tool_execution = {
                "tool_id": "create_study_plan",
                "payload": {
                    "goal": event.payload,
                    "preferred_format": context.agent_memory.get("preferred_format"),
                },
            }
            
            result_event = Event(
                event_type="study_plan_created",
                source_agent="learning_assistant_agent",
                payload={"status": "created"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class WeatherAgent(BaseAgent):
    """Agent for providing weather forecasts and suggesting activities based on weather."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="weather_agent",
            version="1.0.0",
            name="Weather Agent",
            description="Provides weather forecasts, sends weather alerts, and suggests activities based on conditions.",
            inputs={
                "location": {"type": "string", "required": False},
                "alert_preferences": {"type": "object", "required": False},
            },
            outputs={},
            subscribed_events=["calendar_updated"],
            emitted_events=["weather_alert", "activity_suggestion"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["get_forecast", "suggest_activity"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "location": inputs.get("location", ""),
            "alert_preferences": inputs.get("alert_preferences", {}),
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle calendar updates to suggest weather-appropriate activities."""
        if event.event_type == "calendar_updated":
            tool_execution = {
                "tool_id": "get_forecast",
                "payload": {
                    "date": event.payload.get("date"),
                    "location": context.agent_memory.get("location"),
                },
            }
            
            result_event = Event(
                event_type="activity_suggestion",
                source_agent="weather_agent",
                payload={"status": "forecast_checked"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class ShoppingAssistantAgent(BaseAgent):
    """Agent for managing shopping lists, price tracking, and suggesting deals."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="shopping_assistant_agent",
            version="1.0.0",
            name="Shopping Assistant",
            description="Manages your shopping lists, tracks prices, suggests deals, and helps find the best products.",
            inputs={
                "preferred_stores": {"type": "array", "required": False},
                "budget_limit": {"type": "number", "required": False},
            },
            outputs={},
            subscribed_events=["item_needed", "shopping_list_updated"],
            emitted_events=["deal_found", "price_drop_alert"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["track_price", "find_deals"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "preferred_stores": inputs.get("preferred_stores", []),
            "budget_limit": inputs.get("budget_limit", 0),
            "tracked_items": [],
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle shopping-related events."""
        if event.event_type in ["item_needed", "shopping_list_updated"]:
            tool_execution = {
                "tool_id": "find_deals",
                "payload": {
                    "items": event.payload.get("items", []),
                    "preferred_stores": context.agent_memory.get("preferred_stores"),
                    "budget_limit": context.agent_memory.get("budget_limit"),
                },
            }
            
            result_event = Event(
                event_type="deal_found",
                source_agent="shopping_assistant_agent",
                payload={"status": "deals_found"},
            )
            
            return AgentResult(
                tool_executions=[tool_execution],
                events=[result_event],
            )
        
        return AgentResult()


class NewsAggregatorAgent(BaseAgent):
    """Agent for aggregating news, filtering by interests, and providing daily briefings."""
    
    def manifest(self) -> AgentManifest:
        return AgentManifest(
            agent_id="news_aggregator_agent",
            version="1.0.0",
            name="News Aggregator",
            description="Aggregates news from multiple sources, filters by your interests, and provides personalized daily briefings.",
            inputs={
                "interests": {"type": "array", "required": False},
                "briefing_time": {"type": "string", "required": False},
            },
            outputs={},
            subscribed_events=[],
            emitted_events=["daily_briefing_ready", "breaking_news_alert"],
            permissions={
                "read_shared_context": True,
                "write_shared_context": True,
            },
            tools=["aggregate_news", "create_briefing"],
            collaboration_rules={},
        )
    
    def onboard(self, inputs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Initialize agent memory."""
        return {
            "interests": inputs.get("interests", []),
            "briefing_time": inputs.get("briefing_time", "08:00"),
            "onboarded_at": "2024-01-01T00:00:00Z",
        }
    
    def handle_event(self, event: Event, context: AgentContext) -> AgentResult:
        """Handle news aggregation events."""
        return AgentResult()
