# Agent Marketplace Platform

A platform for installing, personalizing, and orchestrating multiple AI agents that collaborate via events under strict governance.

## Features

- **Marketplace**: Browse and install pre-built agents
- **Agent Installation**: Personalized agent onboarding with user inputs
- **Event-Driven Orchestration**: Agents communicate via events in a controlled DAG
- **Tool Execution**: Tools with optional human-in-the-loop approval
- **Full Traceability**: All events and executions are logged for debugging

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Create virtual environment and install dependencies:**

   **Using uv (recommended - faster):**
   ```bash
   # Install Python 3.11 if not already installed
   uv python install 3.11
   
   # Create virtual environment with Python 3.11
   uv venv --python 3.11
   
   # Activate virtual environment
   source .venv/bin/activate
   
   # Install dependencies
   uv pip install -r requirements.txt
   ```

   **Using pip:**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your database and Redis URLs
```

3. **Start PostgreSQL and Redis:**
```bash
# Using Docker Compose
docker-compose up -d
```

4. **Initialize database:**
```bash
# Option 1: Using setup script
python scripts/setup.py

# Option 2: Using Alembic
alembic upgrade head
```

5. **Seed initial data:**
```bash
# Seed tool definitions
python scripts/seed_tool_definitions.py

# Create a test user
python scripts/create_test_user.py
```

6. **Start the server:**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

- **Modular monolith** with event-driven execution
- **FastAPI** for API Gateway
- **PostgreSQL** for primary data storage
- **Redis** for caching hot path data
- **Agent SDK** for building agents
- **Orchestrator** for event-driven agent execution

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Example Usage

### 1. List available agents
```bash
curl http://localhost:8000/api/v1/marketplace/agents
```

### 2. Install an agent
```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/agents/install \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "health_goal_agent",
    "version": "1.0.0",
    "inputs": {
      "target_weight": 70,
      "dietary_preferences": ["vegetarian"]
    }
  }'
```

### 3. Create an event
```bash
curl -X POST http://localhost:8000/api/v1/users/{user_id}/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "health_goal_updated",
    "payload": {
      "target_weight": 70
    }
  }'
```

## Development

### Project Structure

```
clara/
├── app/
│   ├── api/          # FastAPI routes
│   ├── cache/         # Redis cache service
│   ├── models/        # SQLAlchemy models
│   ├── orchestrator/  # Orchestration service
│   ├── sdk/           # Agent SDK
│   ├── tools/         # Tool executor
│   ├── config.py      # Configuration
│   ├── database.py    # Database setup
│   └── main.py        # FastAPI app
├── alembic/           # Database migrations
├── scripts/           # Utility scripts
└── requirements.txt   # Dependencies
```

### Adding a New Agent

1. Create a new agent class inheriting from `BaseAgent`:
```python
from app.sdk.base import BaseAgent
from app.sdk.types import AgentManifest, AgentContext, AgentResult, Event

class MyAgent(BaseAgent):
    def manifest(self) -> AgentManifest:
        # Define agent capabilities
        
    def onboard(self, inputs, context) -> dict:
        # Initialize agent memory
        
    def handle_event(self, event, context) -> AgentResult:
        # Handle events
```

2. Register the agent in `app/main.py` startup event

3. The agent manifest will be automatically seeded to the database

## Testing

```bash
# Run tests (when implemented)
pytest
```

## License

MIT
