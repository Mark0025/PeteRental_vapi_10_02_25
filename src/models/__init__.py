"""
Data models using Pydantic for validation and serialization
"""

from .agent import Agent, AgentCreate, AgentUpdate
from .appointment import Appointment, AppointmentCreate, AppointmentUpdate
from .user import (
    User,
    UserCreate,
    UserUpdate,
    UserPublic,
    UserWithAgents,
    MicrosoftTokenUpdate,
)

__all__ = [
    "Agent",
    "AgentCreate",
    "AgentUpdate",
    "Appointment",
    "AppointmentCreate",
    "AppointmentUpdate",
    "User",
    "UserCreate",
    "UserUpdate",
    "UserPublic",
    "UserWithAgents",
    "MicrosoftTokenUpdate",
]
