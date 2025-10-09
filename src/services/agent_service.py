"""
Agent Service

Business logic layer for agent management.
Orchestrates agent and appointment operations with business rules.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from src.database import Database
from src.models import Agent, AgentCreate, AgentUpdate
from src.models import Appointment, AppointmentCreate
from src.repositories import AgentRepository, AppointmentRepository


class AgentService:
    """
    Service for agent management and business operations

    Provides high-level operations that coordinate multiple repositories
    and enforce business rules.

    Usage:
        ```python
        from src.database import get_database
        from src.services import AgentService

        db = await get_database()
        service = AgentService(db)

        # Register new agent
        agent = await service.register_agent(
            vapi_assistant_id="24464697-8f45-4b38-b43a-d337f50c370e",
            agent_name="Property Manager 1",
            calendar_user_id="mark@peterei.com"
        )

        # Get agent with appointment stats
        agent_info = await service.get_agent_with_stats("agent_24464697")
        ```
    """

    def __init__(self, database: Database):
        """
        Initialize service

        Args:
            database: Database instance
        """
        self.db = database
        self.agent_repo = AgentRepository(database)
        self.appointment_repo = AppointmentRepository(database)

    async def register_agent(
        self,
        vapi_assistant_id: str,
        agent_name: str,
        calendar_user_id: Optional[str] = None,
    ) -> Agent:
        """
        Register a new agent in the system

        Business logic:
        - Check if agent already exists (avoid duplicates)
        - Validate VAPI assistant ID format
        - Create agent with proper defaults

        Args:
            vapi_assistant_id: VAPI platform assistant UUID
            agent_name: Human-readable name
            calendar_user_id: Optional calendar user email

        Returns:
            Created agent

        Raises:
            ValueError: If agent already exists
            Exception: If creation fails

        Example:
            ```python
            agent = await service.register_agent(
                vapi_assistant_id="24464697-8f45-4b38-b43a-d337f50c370e",
                agent_name="Appointment Setter Agent",
                calendar_user_id="mark@peterei.com"
            )
            ```
        """
        # Check if agent already exists
        existing = await self.agent_repo.get_by_vapi_id(vapi_assistant_id)
        if existing:
            raise ValueError(
                f"Agent already registered: {existing.agent_id} ({existing.agent_name})"
            )

        # Create agent
        agent_data = AgentCreate(
            vapi_assistant_id=vapi_assistant_id,
            agent_name=agent_name,
            calendar_user_id=calendar_user_id,
            is_active=True,
        )

        agent = await self.agent_repo.create(agent_data)
        logger.info(
            f"🎉 Registered new agent: {agent.agent_id} - {agent.agent_name}"
        )
        return agent

    async def get_agent_by_vapi_id(self, vapi_assistant_id: str) -> Optional[Agent]:
        """
        Get agent by VAPI assistant ID

        This is the primary lookup method for webhook handlers.

        Args:
            vapi_assistant_id: VAPI platform UUID

        Returns:
            Agent if found, None otherwise
        """
        return await self.agent_repo.get_by_vapi_id(vapi_assistant_id)

    async def get_agent_with_stats(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent information with appointment statistics

        Returns agent data plus appointment counts by status.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with agent data and stats, or None if not found

        Example:
            ```python
            info = await service.get_agent_with_stats("agent_24464697")
            # {
            #     "agent": {...agent data...},
            #     "stats": {
            #         "total": 45,
            #         "confirmed": 12,
            #         "completed": 30,
            #         "cancelled": 2,
            #         "no_show": 1
            #     }
            # }
            ```
        """
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            return None

        stats = await self.appointment_repo.get_agent_stats(agent_id)

        return {
            "agent": agent.model_dump(),
            "stats": stats,
        }

    async def list_active_agents_with_stats(self) -> List[Dict[str, Any]]:
        """
        Get all active agents with their appointment statistics

        Useful for dashboards and analytics.

        Returns:
            List of agent data with stats

        Example:
            ```python
            agents = await service.list_active_agents_with_stats()
            for agent_data in agents:
                print(f"{agent_data['agent']['agent_name']}: {agent_data['stats']['total']} appointments")
            ```
        """
        agents = await self.agent_repo.list_active()
        result = []

        for agent in agents:
            stats = await self.appointment_repo.get_agent_stats(agent.agent_id)
            result.append({"agent": agent.model_dump(), "stats": stats})

        return result

    async def create_appointment(
        self,
        agent_id: str,
        property_address: str,
        start_time: datetime,
        end_time: datetime,
        attendee_name: str,
        attendee_email: Optional[str] = None,
        vapi_call_id: Optional[str] = None,
        calendar_event_id: Optional[str] = None,
    ) -> Appointment:
        """
        Create appointment for an agent

        Business logic:
        - Verify agent exists and is active
        - Validate appointment times
        - Create appointment with proper linking

        Args:
            agent_id: Agent handling the appointment
            property_address: Property to view
            start_time: Appointment start (UTC)
            end_time: Appointment end (UTC)
            attendee_name: Person attending
            attendee_email: Optional email for calendar invite
            vapi_call_id: Optional VAPI call that created this
            calendar_event_id: Optional Microsoft Calendar event ID

        Returns:
            Created appointment

        Raises:
            ValueError: If agent not found or inactive
            Exception: If creation fails

        Example:
            ```python
            appointment = await service.create_appointment(
                agent_id="agent_24464697",
                property_address="123 Main St, Norman, OK",
                start_time=datetime(2025, 10, 10, 14, 0, tzinfo=timezone.utc),
                end_time=datetime(2025, 10, 10, 14, 30, tzinfo=timezone.utc),
                attendee_name="John Doe",
                attendee_email="john@example.com",
                vapi_call_id="call_abc123"
            )
            ```
        """
        # Verify agent exists and is active
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        if not agent.is_active:
            raise ValueError(f"Agent is inactive: {agent_id}")

        # Create appointment
        appointment_data = AppointmentCreate(
            agent_id=agent_id,
            property_address=property_address,
            start_time=start_time,
            end_time=end_time,
            attendee_name=attendee_name,
            attendee_email=attendee_email,
            vapi_call_id=vapi_call_id,
            calendar_event_id=calendar_event_id,
            status="confirmed",
        )

        appointment = await self.appointment_repo.create(appointment_data)
        logger.info(
            f"📅 Created appointment for {agent.agent_name}: "
            f"{attendee_name} at {property_address}"
        )
        return appointment

    async def get_agent_appointments(
        self, agent_id: str, status: Optional[str] = None
    ) -> List[Appointment]:
        """
        Get all appointments for an agent

        Args:
            agent_id: Agent ID
            status: Optional status filter

        Returns:
            List of appointments
        """
        return await self.appointment_repo.get_by_agent(agent_id, status)

    async def get_upcoming_appointments(
        self, agent_id: Optional[str] = None, days_ahead: int = 30
    ) -> List[Appointment]:
        """
        Get upcoming confirmed appointments

        Args:
            agent_id: Optional agent filter
            days_ahead: Days to look ahead (default 30)

        Returns:
            List of upcoming appointments
        """
        return await self.appointment_repo.get_upcoming(agent_id, days_ahead)

    async def update_calendar_user(
        self, agent_id: str, calendar_user_id: str
    ) -> Optional[Agent]:
        """
        Link agent to a calendar user

        Business logic:
        - Verify agent exists
        - Update calendar user association
        - Log the change

        Args:
            agent_id: Agent to update
            calendar_user_id: Calendar user email

        Returns:
            Updated agent if found, None otherwise

        Example:
            ```python
            agent = await service.update_calendar_user(
                "agent_24464697",
                "newuser@peterei.com"
            )
            ```
        """
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            return None

        updated = await self.agent_repo.update(
            agent_id, AgentUpdate(calendar_user_id=calendar_user_id)
        )

        if updated:
            logger.info(
                f"🔗 Linked {agent.agent_name} to calendar user: {calendar_user_id}"
            )

        return updated

    async def deactivate_agent(self, agent_id: str) -> bool:
        """
        Deactivate an agent (soft delete)

        Business logic:
        - Deactivate agent (preserve data and appointments)
        - Log the deactivation

        Args:
            agent_id: Agent to deactivate

        Returns:
            True if successful, False if not found

        Example:
            ```python
            success = await service.deactivate_agent("agent_24464697")
            ```
        """
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            return False

        success = await self.agent_repo.deactivate(agent_id)
        if success:
            logger.info(f"🔴 Deactivated agent: {agent.agent_name}")

        return success

    async def reactivate_agent(self, agent_id: str) -> bool:
        """
        Reactivate a deactivated agent

        Args:
            agent_id: Agent to activate

        Returns:
            True if successful, False if not found
        """
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            return False

        success = await self.agent_repo.activate(agent_id)
        if success:
            logger.info(f"🟢 Reactivated agent: {agent.agent_name}")

        return success

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get overall system statistics

        Returns counts of agents and appointments across the system.

        Returns:
            Dictionary with system-wide stats

        Example:
            ```python
            stats = await service.get_system_stats()
            # {
            #     "agents": {
            #         "total": 5,
            #         "active": 4
            #     },
            #     "appointments": {
            #         "total": 150,
            #         "by_status": {...}
            #     }
            # }
            ```
        """
        total_agents = await self.agent_repo.count_all()
        active_agents = await self.agent_repo.count_active()

        # Get appointment stats across all agents
        agents = await self.agent_repo.list_all()
        total_appointments = 0
        status_counts = {"confirmed": 0, "completed": 0, "cancelled": 0, "no_show": 0}

        for agent in agents:
            stats = await self.appointment_repo.get_agent_stats(agent.agent_id)
            total_appointments += stats.get("total", 0)
            for status in status_counts.keys():
                status_counts[status] += stats.get(status, 0)

        return {
            "agents": {"total": total_agents, "active": active_agents},
            "appointments": {"total": total_appointments, "by_status": status_counts},
        }
