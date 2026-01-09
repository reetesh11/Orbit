# Architecture Overview

This document provides a high-level overview of the Agent Marketplace Platform architecture.

## System Components

### 1. API Gateway (FastAPI)
- **Location**: `app/main.py`, `app/api/routes.py`
- **Purpose**: HTTP API endpoints for marketplace, agent installation, and event processing
- **Key Endpoints**:
  - `GET /api/v1/marketplace/agents` - List available agents
  - `POST /api/v1/users/{user_id}/agents/install` - Install an agent
  - `POST /api/v1/users/{user_id}/events` - Create an event
  - `GET /api/v1/users/{user_id}/tools/pending` - List pending tool approvals

### 2. Orchestrator Service
- **Location**: `app/orchestrator/service.py`
- **Purpose**: Handles agent installation and event-driven execution
- **Key Responsibilities**:
  - Agent installation flow (Section 9)
  - Event processing and agent execution (Section 10)
  - Inter-agent communication via events (Section 11)
  - Context management (shared context, agent memory)

### 3. Agent SDK
- **Location**: `app/sdk/`
- **Purpose**: Base classes and types for building agents
- **Key Components**:
  - `BaseAgent` - Abstract base class for all agents
  - `AgentManifest` - Agent capability definition
  - `AgentContext` - Context passed to agents
  - `AgentResult` - Structured output from agents

### 4. Tool Executor
- **Location**: `app/tools/executor.py`
- **Purpose**: Executes tools with human-in-the-loop support
- **Key Features**:
  - Tool execution with approval workflow
  - Human approval tracking
  - Tool registry for implementations

### 5. Cache Service (Redis)
- **Location**: `app/cache/service.py`
- **Purpose**: Caching for hot path data
- **Cached Data**:
  - Agent manifests
  - User installations
  - Shared context

### 6. Database Models
- **Location**: `app/models/`
- **Purpose**: SQLAlchemy models for all domain entities
- **Key Models**:
  - `User`, `UserProfile`, `SharedContext`
  - `AgentManifest`, `AgentInstallation`, `AgentContext`
  - `Event`, `ExecutionTrace`
  - `ToolDefinition`, `ToolExecution`, `HumanApproval`

## Data Flow

### Agent Installation Flow
1. User requests agent installation via API
2. Orchestrator fetches agent manifest
3. Orchestrator calls `agent.onboard()` with user inputs
4. Agent returns initial memory state
5. Orchestrator creates `AgentInstallation` and `AgentContext`
6. Installation marked as active

### Event Processing Flow
1. Event created (user-initiated or agent-emitted)
2. Event persisted to database
3. Orchestrator finds subscribed agents
4. For each subscribed agent:
   - Load agent context (user_profile, shared_context, agent_memory, recent_events)
   - Execute `agent.handle_event()`
   - Apply context updates
   - Create tool executions
   - Collect new events
5. Process new events recursively (controlled DAG)
6. Execution traces logged for observability

### Tool Execution Flow
1. Agent returns tool execution request in `AgentResult`
2. Orchestrator creates `ToolExecution` record
3. If approval required:
   - Status set to "pending"
   - Human approval required
4. If approved or no approval needed:
   - Tool executed via `ToolRegistry`
   - Status updated to "completed" or "failed"

## Key Design Principles

1. **Agents are Pure Logic**: No direct DB, network, or tool access
2. **Event-Driven**: All inter-agent communication via events
3. **Deterministic**: Agents receive structured inputs, return structured outputs
4. **Auditable**: All events and executions are logged
5. **Safe**: Manifest-driven permissions, orchestrator validates all writes

## Security & Permissions

- Agent permissions defined in manifest
- Orchestrator enforces permissions
- Tools executed via allow-list registry
- Human approval for high-risk operations

## Scalability Considerations

- Redis caching for hot path
- Database indexes on key queries
- Event-driven architecture supports horizontal scaling
- Modular design allows service extraction
