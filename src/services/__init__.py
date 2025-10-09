"""
Service Layer

Business logic for agent and appointment management.
Orchestrates repository operations and enforces business rules.
"""

from .agent_service import AgentService

__all__ = ["AgentService"]
