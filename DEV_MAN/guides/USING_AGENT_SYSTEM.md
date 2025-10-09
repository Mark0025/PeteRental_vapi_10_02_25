# Using the Agent System

**Quick reference for working with the multi-agent architecture**

## 📋 Overview

The agent system uses clean architecture with clear separation of concerns:

```
Models (Pydantic) → Repositories (Data Access) → Services (Business Logic) → API Endpoints
```

## 🚀 Quick Start

### Basic Agent Operations

```python
from src.database import get_database
from src.services import AgentService

# Initialize
db = await get_database()
service = AgentService(db)

# Register new agent
agent = await service.register_agent(
    vapi_assistant_id="24464697-8f45-4b38-b43a-d337f50c370e",
    agent_name="Property Manager 1",
    calendar_user_id="mark@peterei.com"
)

# Get agent by VAPI ID (webhook use case)
agent = await service.get_agent_by_vapi_id("24464697-8f45-4b38-b43a-d337f50c370e")
if agent:
    print(f"Found: {agent.agent_name}")

# Get agent with statistics
agent_info = await service.get_agent_with_stats("agent_24464697")
print(f"Total appointments: {agent_info['stats']['total']}")
```

### Creating Appointments

```python
from datetime import datetime, timedelta, timezone

# Create appointment for agent
appointment = await service.create_appointment(
    agent_id="agent_24464697",
    property_address="123 Main St, Norman, OK 73069",
    start_time=datetime.now(timezone.utc) + timedelta(days=1, hours=14),
    end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=14, minutes=30),
    attendee_name="John Doe",
    attendee_email="john@example.com",
    vapi_call_id="call_abc123",  # From VAPI webhook
    calendar_event_id="AAMkAGI2..."  # From Microsoft Calendar
)
```

### Querying Appointments

```python
# Get all appointments for an agent
appointments = await service.get_agent_appointments("agent_24464697")

# Get only confirmed appointments
confirmed = await service.get_agent_appointments("agent_24464697", status="confirmed")

# Get upcoming appointments (next 30 days)
upcoming = await service.get_upcoming_appointments("agent_24464697")

# Get upcoming for next 7 days
next_week = await service.get_upcoming_appointments("agent_24464697", days_ahead=7)
```

## 🔧 Architecture Layers

### 1. Models Layer (`src/models/`)

**Pydantic models with validation**

```python
from src.models import Agent, AgentCreate, AgentUpdate
from src.models import Appointment, AppointmentCreate, AppointmentUpdate

# Create models validate automatically
agent_data = AgentCreate(
    agent_name="Test Agent",
    vapi_assistant_id="12345678-1234-1234-1234-123456789012",  # Must be valid UUID
    calendar_user_id="test@example.com"  # Optional
)

# Update models support partial updates
update_data = AgentUpdate(
    calendar_user_id="new@example.com"  # Only update calendar user
)
```

**Available Models:**

- `AgentBase` - Base fields
- `AgentCreate` - For creating agents
- `AgentUpdate` - For updating agents (partial updates)
- `Agent` - Full agent with ID and timestamps
- `AppointmentBase` - Base appointment fields
- `AppointmentCreate` - For creating appointments
- `AppointmentUpdate` - For updating appointments
- `Appointment` - Full appointment with ID

### 2. Repository Layer (`src/repositories/`)

**Data access objects (direct database operations)**

```python
from src.repositories import AgentRepository, AppointmentRepository

db = await get_database()
agent_repo = AgentRepository(db)
appointment_repo = AppointmentRepository(db)

# Agent repository methods
agent = await agent_repo.create(agent_data)
agent = await agent_repo.get_by_id("agent_24464697")
agent = await agent_repo.get_by_vapi_id("24464697-8f45-4b38-b43a-d337f50c370e")
agents = await agent_repo.list_active()
agents = await agent_repo.get_by_calendar_user("mark@peterei.com")
updated = await agent_repo.update("agent_24464697", update_data)
success = await agent_repo.deactivate("agent_24464697")  # Soft delete
exists = await agent_repo.exists("24464697-8f45-4b38-b43a-d337f50c370e")

# Appointment repository methods
appointment = await appointment_repo.create(appointment_data)
appointment = await appointment_repo.get_by_id(123)
appointments = await appointment_repo.get_by_agent("agent_24464697")
appointments = await appointment_repo.get_by_agent("agent_24464697", status="confirmed")
appointment = await appointment_repo.get_by_vapi_call("call_abc123")
appointment = await appointment_repo.get_by_calendar_event("AAMkAGI2...")
upcoming = await appointment_repo.get_upcoming("agent_24464697", days_ahead=7)
stats = await appointment_repo.get_agent_stats("agent_24464697")
```

### 3. Service Layer (`src/services/`)

**Business logic (high-level operations)**

Use services for:
- Complex operations involving multiple repositories
- Business rule enforcement
- Coordinated actions

```python
from src.services import AgentService

service = AgentService(db)

# High-level operations
agent = await service.register_agent(...)  # Checks for duplicates
agent_info = await service.get_agent_with_stats(...)  # Combines data
appointment = await service.create_appointment(...)  # Validates agent exists
success = await service.deactivate_agent(...)  # Soft delete with logging
system_stats = await service.get_system_stats()  # Cross-repository analytics
```

## 🎯 Common Use Cases

### Use Case 1: VAPI Webhook Handler

**Extract agent from incoming VAPI call:**

```python
from fastapi import Request
from src.database import get_database
from src.services import AgentService

@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    data = await request.json()

    # Extract VAPI assistant ID from call
    vapi_assistant_id = data.get("assistant", {}).get("id")

    if not vapi_assistant_id:
        return {"error": "No assistant ID in call"}

    # Look up agent
    db = await get_database()
    service = AgentService(db)

    agent = await service.get_agent_by_vapi_id(vapi_assistant_id)

    if not agent:
        return {"error": f"Agent not found: {vapi_assistant_id}"}

    # Use agent for appointment
    print(f"Call handled by: {agent.agent_name}")
    print(f"Calendar user: {agent.calendar_user_id}")

    return {"agent": agent.agent_id, "message": "Call received"}
```

### Use Case 2: Create Appointment from VAPI Call

**When VAPI function call creates appointment:**

```python
@app.post("/vapi/function/set_appointment")
async def set_appointment(request: Request):
    data = await request.json()

    # Extract data from VAPI function call
    vapi_assistant_id = data.get("assistant", {}).get("id")
    vapi_call_id = data.get("call", {}).get("id")

    # Function parameters
    params = data.get("parameters", {})
    property_address = params.get("property_address")
    start_time = datetime.fromisoformat(params.get("start_time"))
    end_time = datetime.fromisoformat(params.get("end_time"))
    attendee_name = params.get("attendee_name")
    attendee_email = params.get("attendee_email")

    # Get agent
    db = await get_database()
    service = AgentService(db)
    agent = await service.get_agent_by_vapi_id(vapi_assistant_id)

    if not agent:
        return {"error": "Agent not found"}

    # Create appointment
    appointment = await service.create_appointment(
        agent_id=agent.agent_id,
        property_address=property_address,
        start_time=start_time,
        end_time=end_time,
        attendee_name=attendee_name,
        attendee_email=attendee_email,
        vapi_call_id=vapi_call_id
    )

    return {
        "success": True,
        "appointment_id": appointment.id,
        "agent": agent.agent_name
    }
```

### Use Case 3: Agent Dashboard

**Show agent performance:**

```python
@app.get("/dashboard/agents")
async def agent_dashboard():
    db = await get_database()
    service = AgentService(db)

    # Get all active agents with stats
    agents = await service.list_active_agents_with_stats()

    return {
        "agents": [
            {
                "name": a["agent"]["agent_name"],
                "total_appointments": a["stats"]["total"],
                "confirmed": a["stats"]["confirmed"],
                "completed": a["stats"]["completed"]
            }
            for a in agents
        ]
    }
```

### Use Case 4: System Analytics

**Overall system performance:**

```python
@app.get("/dashboard/stats")
async def system_stats():
    db = await get_database()
    service = AgentService(db)

    stats = await service.get_system_stats()

    return {
        "agents": {
            "total": stats["agents"]["total"],
            "active": stats["agents"]["active"]
        },
        "appointments": {
            "total": stats["appointments"]["total"],
            "confirmed": stats["appointments"]["by_status"]["confirmed"],
            "completed": stats["appointments"]["by_status"]["completed"]
        }
    }
```

## 🔐 Best Practices

### 1. Always Use Services for Business Logic

**❌ Don't:**
```python
# Mixing business logic in endpoints
agent_repo = AgentRepository(db)
agent = await agent_repo.create(agent_data)  # No duplicate check!
```

**✅ Do:**
```python
# Use service which checks for duplicates
service = AgentService(db)
agent = await service.register_agent(...)  # Enforces business rules
```

### 2. Use Repositories for Direct Data Access

**When you need simple CRUD without business logic:**

```python
# Simple lookup - use repository directly
agent_repo = AgentRepository(db)
agent = await agent_repo.get_by_id("agent_24464697")

# Complex operation - use service
service = AgentService(db)
agent_info = await service.get_agent_with_stats("agent_24464697")
```

### 3. Let Pydantic Validate

**Models validate automatically:**

```python
try:
    agent_data = AgentCreate(
        agent_name="Test",
        vapi_assistant_id="invalid-uuid",  # Will fail validation
        calendar_user_id="not-an-email"     # Will fail validation
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

### 4. Use Soft Deletes

**Preserve data and history:**

```python
# ❌ Don't hard delete
await agent_repo.delete("agent_24464697")  # Destroys all data

# ✅ Do soft delete
await service.deactivate_agent("agent_24464697")  # Preserves history
```

### 5. Handle Timezone Properly

**Always use UTC in database:**

```python
from datetime import datetime, timezone

# ✅ Correct - UTC timezone
start_time = datetime.now(timezone.utc)

# ❌ Wrong - naive datetime
start_time = datetime.now()  # Ambiguous timezone
```

## 📊 Database Schema Reference

```sql
-- Agents table
agents
  ├── agent_id (VARCHAR PRIMARY KEY)           -- "agent_24464697"
  ├── vapi_assistant_id (VARCHAR UNIQUE)       -- VAPI UUID
  ├── agent_name (VARCHAR)                     -- Human-readable name
  ├── calendar_user_id (VARCHAR)               -- Email
  ├── is_active (BOOLEAN)                      -- Soft delete flag
  ├── created_at (TIMESTAMP)
  └── updated_at (TIMESTAMP)

-- Appointments table
appointments
  ├── id (SERIAL PRIMARY KEY)
  ├── agent_id (VARCHAR FK → agents.agent_id)
  ├── vapi_call_id (VARCHAR)
  ├── property_address (TEXT)
  ├── start_time (TIMESTAMP)
  ├── end_time (TIMESTAMP)
  ├── attendee_name (VARCHAR)
  ├── attendee_email (VARCHAR)
  ├── status (VARCHAR CHECK)                   -- confirmed, cancelled, completed, no_show
  ├── calendar_event_id (VARCHAR)
  └── created_at (TIMESTAMP)
```

## 🧪 Testing

```bash
# Run full integration tests (requires DATABASE_URL)
python test_agent_system.py

# Expected output:
# ✅ Agent Registration
# ✅ Agent Lookup
# ✅ Appointment Creation
# ✅ Appointment Queries
# ✅ Agent Statistics
# ✅ System Statistics
# ✅ Agent Deactivation
# 🎉 ALL TESTS PASSED
```

## 📚 Related Documentation

- [DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md) - Migration system
- [COMPLETE_SYSTEM_ANALYSIS.md](../COMPLETE_SYSTEM_ANALYSIS.md) - Full architecture
- [API_DOCS.md](../reference/API_DOCS.md) - API reference

---

**Created:** 2025-10-09
**Last Updated:** 2025-10-09
**Status:** ✅ Production Ready
