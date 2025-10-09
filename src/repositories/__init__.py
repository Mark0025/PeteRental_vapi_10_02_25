"""
Repository Layer

Data access objects (DAOs) for database operations.
Implements repository pattern for clean separation of concerns.
"""

from .agent_repository import AgentRepository
from .appointment_repository import AppointmentRepository

__all__ = ["AgentRepository", "AppointmentRepository"]
