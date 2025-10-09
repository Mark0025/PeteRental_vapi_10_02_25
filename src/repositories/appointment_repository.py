"""
Appointment Repository

Data access layer for appointment operations.
Handles property viewing appointments linked to agents.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from src.database import Database
from src.models import Appointment, AppointmentCreate, AppointmentUpdate


class AppointmentRepository:
    """
    Repository for appointment database operations

    Usage:
        ```python
        from src.database import get_database
        from src.repositories import AppointmentRepository

        db = await get_database()
        repo = AppointmentRepository(db)

        # Create appointment
        appt = await repo.create(AppointmentCreate(
            agent_id="agent_24464697",
            property_address="123 Main St, Norman, OK",
            start_time=datetime(2025, 10, 10, 14, 0),
            end_time=datetime(2025, 10, 10, 14, 30),
            attendee_name="John Doe",
            attendee_email="john@example.com"
        ))

        # Get agent's appointments
        appointments = await repo.get_by_agent("agent_24464697")
        ```
    """

    def __init__(self, database: Database):
        """
        Initialize repository

        Args:
            database: Database instance
        """
        self.db = database

    async def create(self, appointment_data: AppointmentCreate) -> Appointment:
        """
        Create a new appointment

        Args:
            appointment_data: Appointment creation data

        Returns:
            Created appointment with generated ID

        Raises:
            Exception: If foreign key constraint fails (agent doesn't exist)
        """
        query = """
            INSERT INTO appointments (
                agent_id, property_address, start_time, end_time,
                attendee_name, attendee_email, status,
                vapi_call_id, calendar_event_id
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(
                query,
                appointment_data.agent_id,
                appointment_data.property_address,
                appointment_data.start_time,
                appointment_data.end_time,
                appointment_data.attendee_name,
                appointment_data.attendee_email,
                appointment_data.status,
                appointment_data.vapi_call_id,
                appointment_data.calendar_event_id,
            )

            if not row:
                raise Exception("Failed to create appointment")

            appointment = Appointment(**dict(row))
            logger.info(
                f"✅ Created appointment #{appointment.id} for {appointment.attendee_name} "
                f"at {appointment.property_address}"
            )
            return appointment

        except Exception as e:
            logger.error(f"❌ Failed to create appointment: {e}")
            raise

    async def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """
        Get appointment by ID

        Args:
            appointment_id: Appointment ID

        Returns:
            Appointment if found, None otherwise
        """
        query = "SELECT * FROM appointments WHERE id = $1"
        row = await self.db.fetchrow(query, appointment_id)

        if row:
            return Appointment(**dict(row))
        return None

    async def get_by_agent(
        self, agent_id: str, status: Optional[str] = None
    ) -> List[Appointment]:
        """
        Get all appointments for an agent

        Args:
            agent_id: Agent ID
            status: Optional status filter (confirmed, cancelled, completed, no_show)

        Returns:
            List of appointments ordered by start_time

        Example:
            ```python
            # All appointments
            all_appts = await repo.get_by_agent("agent_24464697")

            # Only confirmed
            confirmed = await repo.get_by_agent("agent_24464697", status="confirmed")
            ```
        """
        if status:
            query = """
                SELECT * FROM appointments
                WHERE agent_id = $1 AND status = $2
                ORDER BY start_time DESC
            """
            rows = await self.db.fetch(query, agent_id, status)
        else:
            query = """
                SELECT * FROM appointments
                WHERE agent_id = $1
                ORDER BY start_time DESC
            """
            rows = await self.db.fetch(query, agent_id)

        return [Appointment(**dict(row)) for row in rows]

    async def get_by_vapi_call(self, vapi_call_id: str) -> Optional[Appointment]:
        """
        Get appointment by VAPI call ID

        Useful for tracking which call created which appointment.

        Args:
            vapi_call_id: VAPI call identifier

        Returns:
            Appointment if found, None otherwise
        """
        query = "SELECT * FROM appointments WHERE vapi_call_id = $1"
        row = await self.db.fetchrow(query, vapi_call_id)

        if row:
            return Appointment(**dict(row))
        return None

    async def get_by_calendar_event(self, calendar_event_id: str) -> Optional[Appointment]:
        """
        Get appointment by Microsoft Calendar event ID

        Useful for syncing with calendar changes.

        Args:
            calendar_event_id: Microsoft Calendar event ID

        Returns:
            Appointment if found, None otherwise
        """
        query = "SELECT * FROM appointments WHERE calendar_event_id = $1"
        row = await self.db.fetchrow(query, calendar_event_id)

        if row:
            return Appointment(**dict(row))
        return None

    async def get_upcoming(
        self, agent_id: Optional[str] = None, days_ahead: int = 30
    ) -> List[Appointment]:
        """
        Get upcoming appointments

        Args:
            agent_id: Optional agent filter
            days_ahead: How many days to look ahead (default 30)

        Returns:
            List of upcoming confirmed appointments

        Example:
            ```python
            # Next 30 days for all agents
            upcoming = await repo.get_upcoming()

            # Next 7 days for specific agent
            upcoming = await repo.get_upcoming("agent_24464697", days_ahead=7)
            ```
        """
        cutoff = datetime.utcnow() + timedelta(days=days_ahead)

        if agent_id:
            query = """
                SELECT * FROM appointments
                WHERE agent_id = $1
                  AND start_time >= NOW()
                  AND start_time <= $2
                  AND status = 'confirmed'
                ORDER BY start_time ASC
            """
            rows = await self.db.fetch(query, agent_id, cutoff)
        else:
            query = """
                SELECT * FROM appointments
                WHERE start_time >= NOW()
                  AND start_time <= $1
                  AND status = 'confirmed'
                ORDER BY start_time ASC
            """
            rows = await self.db.fetch(query, cutoff)

        return [Appointment(**dict(row)) for row in rows]

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        agent_id: Optional[str] = None,
    ) -> List[Appointment]:
        """
        Get appointments in a date range

        Args:
            start_date: Start of range
            end_date: End of range
            agent_id: Optional agent filter

        Returns:
            List of appointments in range
        """
        if agent_id:
            query = """
                SELECT * FROM appointments
                WHERE agent_id = $1
                  AND start_time >= $2
                  AND start_time < $3
                ORDER BY start_time ASC
            """
            rows = await self.db.fetch(query, agent_id, start_date, end_date)
        else:
            query = """
                SELECT * FROM appointments
                WHERE start_time >= $1
                  AND start_time < $2
                ORDER BY start_time ASC
            """
            rows = await self.db.fetch(query, start_date, end_date)

        return [Appointment(**dict(row)) for row in rows]

    async def update(
        self, appointment_id: int, update_data: AppointmentUpdate
    ) -> Optional[Appointment]:
        """
        Update appointment information

        Args:
            appointment_id: Appointment to update
            update_data: Fields to update (partial updates supported)

        Returns:
            Updated appointment if found, None otherwise

        Example:
            ```python
            # Cancel appointment
            cancelled = await repo.update(
                123,
                AppointmentUpdate(status="cancelled")
            )

            # Update calendar event ID after sync
            synced = await repo.update(
                123,
                AppointmentUpdate(calendar_event_id="AAMkAGI2...")
            )
            ```
        """
        update_fields = update_data.model_dump(exclude_unset=True)

        if not update_fields:
            existing = await self.get_by_id(appointment_id)
            return existing

        # Build SET clause
        set_clause = ", ".join(
            f"{field} = ${i + 2}" for i, field in enumerate(update_fields.keys())
        )
        values = [appointment_id] + list(update_fields.values())

        query = f"""
            UPDATE appointments
            SET {set_clause}
            WHERE id = $1
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(query, *values)

            if not row:
                logger.warning(f"⚠️  Appointment not found: {appointment_id}")
                return None

            appointment = Appointment(**dict(row))
            logger.info(f"✅ Updated appointment #{appointment.id}")
            return appointment

        except Exception as e:
            logger.error(f"❌ Failed to update appointment {appointment_id}: {e}")
            raise

    async def cancel(self, appointment_id: int) -> Optional[Appointment]:
        """
        Cancel an appointment

        Convenience method for updating status to 'cancelled'.

        Args:
            appointment_id: Appointment to cancel

        Returns:
            Updated appointment if found, None otherwise
        """
        return await self.update(appointment_id, AppointmentUpdate(status="cancelled"))

    async def complete(self, appointment_id: int) -> Optional[Appointment]:
        """
        Mark appointment as completed

        Args:
            appointment_id: Appointment to complete

        Returns:
            Updated appointment if found, None otherwise
        """
        return await self.update(appointment_id, AppointmentUpdate(status="completed"))

    async def mark_no_show(self, appointment_id: int) -> Optional[Appointment]:
        """
        Mark appointment as no-show

        Args:
            appointment_id: Appointment to mark

        Returns:
            Updated appointment if found, None otherwise
        """
        return await self.update(appointment_id, AppointmentUpdate(status="no_show"))

    async def delete(self, appointment_id: int) -> bool:
        """
        Hard delete appointment from database

        ⚠️  WARNING: This permanently deletes the appointment.
        Use cancel() for soft delete instead.

        Args:
            appointment_id: Appointment to delete

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM appointments WHERE id = $1"

        try:
            result = await self.db.execute(query, appointment_id)
            deleted = "DELETE 1" in result
            if deleted:
                logger.warning(f"⚠️  HARD DELETED appointment: {appointment_id}")
            return deleted

        except Exception as e:
            logger.error(f"❌ Failed to delete appointment {appointment_id}: {e}")
            raise

    async def count_by_agent(
        self, agent_id: str, status: Optional[str] = None
    ) -> int:
        """
        Count appointments for an agent

        Args:
            agent_id: Agent ID
            status: Optional status filter

        Returns:
            Number of appointments
        """
        if status:
            query = """
                SELECT COUNT(*) FROM appointments
                WHERE agent_id = $1 AND status = $2
            """
            return await self.db.fetchval(query, agent_id, status)
        else:
            query = "SELECT COUNT(*) FROM appointments WHERE agent_id = $1"
            return await self.db.fetchval(query, agent_id)

    async def get_agent_stats(self, agent_id: str) -> dict:
        """
        Get appointment statistics for an agent

        Returns counts by status and total appointments.

        Args:
            agent_id: Agent ID

        Returns:
            Dictionary with stats

        Example:
            ```python
            stats = await repo.get_agent_stats("agent_24464697")
            # {
            #     "total": 45,
            #     "confirmed": 12,
            #     "completed": 30,
            #     "cancelled": 2,
            #     "no_show": 1
            # }
            ```
        """
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed,
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
                COUNT(*) FILTER (WHERE status = 'no_show') as no_show
            FROM appointments
            WHERE agent_id = $1
        """
        row = await self.db.fetchrow(query, agent_id)
        return dict(row) if row else {}
