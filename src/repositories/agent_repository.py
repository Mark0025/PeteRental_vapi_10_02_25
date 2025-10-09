"""
Agent Repository

Data access layer for agent operations.
Provides clean, semantic methods for agent CRUD operations.
"""

from typing import List, Optional
from datetime import datetime
from loguru import logger

from src.database import Database
from src.models import Agent, AgentCreate, AgentUpdate


class AgentRepository:
    """
    Repository for agent database operations

    Usage:
        ```python
        from src.database import get_database
        from src.repositories import AgentRepository

        db = await get_database()
        repo = AgentRepository(db)

        # Create agent
        agent = await repo.create(AgentCreate(
            agent_name="Property Manager 1",
            vapi_assistant_id="24464697-8f45-4b38-b43a-d337f50c370e",
            calendar_user_id="mark@peterei.com"
        ))

        # Get by VAPI ID
        agent = await repo.get_by_vapi_id("24464697-8f45-4b38-b43a-d337f50c370e")
        ```
    """

    def __init__(self, database: Database):
        """
        Initialize repository

        Args:
            database: Database instance
        """
        self.db = database

    async def create(self, agent_data: AgentCreate) -> Agent:
        """
        Create a new agent

        Args:
            agent_data: Agent creation data

        Returns:
            Created agent with generated agent_id

        Raises:
            Exception: If agent with same vapi_assistant_id exists
        """
        # Generate agent_id from VAPI assistant ID
        # Format: agent_{first_8_chars_of_uuid}
        agent_id = f"agent_{agent_data.vapi_assistant_id.split('-')[0]}"

        query = """
            INSERT INTO agents (
                agent_id, vapi_assistant_id, agent_name,
                calendar_user_id, is_active
            )
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(
                query,
                agent_id,
                agent_data.vapi_assistant_id,
                agent_data.agent_name,
                agent_data.calendar_user_id,
                agent_data.is_active,
            )

            if not row:
                raise Exception("Failed to create agent")

            agent = Agent(**dict(row))
            logger.info(f"✅ Created agent: {agent.agent_id} ({agent.agent_name})")
            return agent

        except Exception as e:
            logger.error(f"❌ Failed to create agent: {e}")
            raise

    async def get_by_id(self, agent_id: str) -> Optional[Agent]:
        """
        Get agent by internal agent_id

        Args:
            agent_id: Internal agent identifier

        Returns:
            Agent if found, None otherwise
        """
        query = "SELECT * FROM agents WHERE agent_id = $1"
        row = await self.db.fetchrow(query, agent_id)

        if row:
            return Agent(**dict(row))
        return None

    async def get_by_vapi_id(self, vapi_assistant_id: str) -> Optional[Agent]:
        """
        Get agent by VAPI assistant ID

        This is the primary lookup method for webhook handlers.

        Args:
            vapi_assistant_id: VAPI platform assistant UUID

        Returns:
            Agent if found, None otherwise

        Example:
            ```python
            # In VAPI webhook handler
            agent = await repo.get_by_vapi_id("24464697-8f45-4b38-b43a-d337f50c370e")
            if agent:
                print(f"Found agent: {agent.agent_name}")
            ```
        """
        query = "SELECT * FROM agents WHERE vapi_assistant_id = $1"
        row = await self.db.fetchrow(query, vapi_assistant_id)

        if row:
            return Agent(**dict(row))
        return None

    async def get_by_calendar_user(self, calendar_user_id: str) -> List[Agent]:
        """
        Get all agents for a specific calendar user

        Useful for multi-user systems where one user manages multiple agents.

        Args:
            calendar_user_id: Calendar user email

        Returns:
            List of agents (may be empty)
        """
        query = """
            SELECT * FROM agents
            WHERE calendar_user_id = $1
            ORDER BY created_at DESC
        """
        rows = await self.db.fetch(query, calendar_user_id)
        return [Agent(**dict(row)) for row in rows]

    async def list_active(self) -> List[Agent]:
        """
        Get all active agents

        Returns:
            List of active agents ordered by creation date
        """
        query = """
            SELECT * FROM agents
            WHERE is_active = TRUE
            ORDER BY created_at DESC
        """
        rows = await self.db.fetch(query)
        return [Agent(**dict(row)) for row in rows]

    async def list_all(self) -> List[Agent]:
        """
        Get all agents (including inactive)

        Returns:
            List of all agents ordered by creation date
        """
        query = "SELECT * FROM agents ORDER BY created_at DESC"
        rows = await self.db.fetch(query)
        return [Agent(**dict(row)) for row in rows]

    async def update(self, agent_id: str, update_data: AgentUpdate) -> Optional[Agent]:
        """
        Update agent information

        Only updates fields provided in update_data (partial updates supported).

        Args:
            agent_id: Agent to update
            update_data: Fields to update

        Returns:
            Updated agent if found, None otherwise

        Example:
            ```python
            # Update only the calendar user
            updated = await repo.update(
                "agent_24464697",
                AgentUpdate(calendar_user_id="new@email.com")
            )
            ```
        """
        # Build dynamic UPDATE query for provided fields
        update_fields = update_data.model_dump(exclude_unset=True)

        if not update_fields:
            # Nothing to update
            existing = await self.get_by_id(agent_id)
            return existing

        # Always update updated_at timestamp
        update_fields["updated_at"] = datetime.utcnow()

        # Build SET clause
        set_clause = ", ".join(
            f"{field} = ${i + 2}" for i, field in enumerate(update_fields.keys())
        )
        values = [agent_id] + list(update_fields.values())

        query = f"""
            UPDATE agents
            SET {set_clause}
            WHERE agent_id = $1
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(query, *values)

            if not row:
                logger.warning(f"⚠️  Agent not found: {agent_id}")
                return None

            agent = Agent(**dict(row))
            logger.info(f"✅ Updated agent: {agent.agent_id}")
            return agent

        except Exception as e:
            logger.error(f"❌ Failed to update agent {agent_id}: {e}")
            raise

    async def deactivate(self, agent_id: str) -> bool:
        """
        Soft delete agent by setting is_active = False

        Preserves agent data and appointment history.

        Args:
            agent_id: Agent to deactivate

        Returns:
            True if deactivated, False if not found

        Example:
            ```python
            # Soft delete instead of hard delete
            success = await repo.deactivate("agent_24464697")
            ```
        """
        updated = await self.update(agent_id, AgentUpdate(is_active=False))
        return updated is not None

    async def activate(self, agent_id: str) -> bool:
        """
        Reactivate a deactivated agent

        Args:
            agent_id: Agent to activate

        Returns:
            True if activated, False if not found
        """
        updated = await self.update(agent_id, AgentUpdate(is_active=True))
        return updated is not None

    async def delete(self, agent_id: str) -> bool:
        """
        Hard delete agent from database

        ⚠️  WARNING: This permanently deletes the agent and cascades to appointments.
        Use deactivate() for soft delete instead.

        Args:
            agent_id: Agent to delete

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM agents WHERE agent_id = $1"

        try:
            result = await self.db.execute(query, agent_id)
            deleted = "DELETE 1" in result
            if deleted:
                logger.warning(f"⚠️  HARD DELETED agent: {agent_id}")
            return deleted

        except Exception as e:
            logger.error(f"❌ Failed to delete agent {agent_id}: {e}")
            raise

    async def exists(self, vapi_assistant_id: str) -> bool:
        """
        Check if agent exists by VAPI assistant ID

        Useful for avoiding duplicate agents.

        Args:
            vapi_assistant_id: VAPI assistant UUID

        Returns:
            True if exists, False otherwise

        Example:
            ```python
            if not await repo.exists(vapi_id):
                await repo.create(agent_data)
            ```
        """
        query = "SELECT EXISTS(SELECT 1 FROM agents WHERE vapi_assistant_id = $1)"
        return await self.db.fetchval(query, vapi_assistant_id)

    async def count_active(self) -> int:
        """
        Count active agents

        Returns:
            Number of active agents
        """
        query = "SELECT COUNT(*) FROM agents WHERE is_active = TRUE"
        return await self.db.fetchval(query)

    async def count_all(self) -> int:
        """
        Count all agents (including inactive)

        Returns:
            Total number of agents
        """
        query = "SELECT COUNT(*) FROM agents"
        return await self.db.fetchval(query)
