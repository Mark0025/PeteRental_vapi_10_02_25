"""
Data models using Pydantic for validation and serialization
"""

from .agent import Agent, AgentCreate, AgentUpdate
from .appointment import Appointment, AppointmentCreate, AppointmentUpdate

__all__ = [
    "Agent",
    "AgentCreate",
    "AgentUpdate",
    "Appointment",
    "AppointmentCreate",
    "AppointmentUpdate",
]
