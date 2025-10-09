"""
Appointment Data Models

Pydantic models for property viewing appointments with validation.
Ensures data integrity for appointment scheduling.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict


class AppointmentBase(BaseModel):
    """Base appointment model with common fields"""

    agent_id: str = Field(..., description="Agent who handled this appointment")
    property_address: str = Field(
        ..., min_length=1, max_length=500, description="Property address for viewing"
    )
    start_time: datetime = Field(..., description="Appointment start time (UTC)")
    end_time: datetime = Field(..., description="Appointment end time (UTC)")
    attendee_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of person attending"
    )
    attendee_email: Optional[EmailStr] = Field(
        None, description="Email for calendar invitation"
    )
    status: str = Field(
        default="confirmed",
        description="Appointment status: confirmed, cancelled, completed",
    )
    vapi_call_id: Optional[str] = Field(
        None, max_length=255, description="VAPI call ID that created this appointment"
    )
    calendar_event_id: Optional[str] = Field(
        None, max_length=255, description="Microsoft Calendar event ID"
    )

    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        """Ensure end_time is after start_time"""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is valid"""
        allowed = {"confirmed", "cancelled", "completed", "no_show"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {allowed}")
        return v


class AppointmentCreate(AppointmentBase):
    """
    Model for creating a new appointment

    Example:
        ```python
        appointment = AppointmentCreate(
            agent_id="agent_24464697",
            property_address="123 Main St, Norman, OK",
            start_time=datetime(2025, 10, 10, 14, 0),
            end_time=datetime(2025, 10, 10, 14, 30),
            attendee_name="John Doe",
            attendee_email="john@example.com",
            vapi_call_id="call_abc123"
        )
        ```
    """

    pass


class AppointmentUpdate(BaseModel):
    """
    Model for updating an existing appointment
    All fields are optional to support partial updates
    """

    property_address: Optional[str] = Field(None, min_length=1, max_length=500)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    attendee_name: Optional[str] = Field(None, min_length=1, max_length=255)
    attendee_email: Optional[EmailStr] = None
    status: Optional[str] = None
    calendar_event_id: Optional[str] = Field(None, max_length=255)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Ensure status is valid if provided"""
        if v is not None:
            allowed = {"confirmed", "cancelled", "completed", "no_show"}
            if v not in allowed:
                raise ValueError(f"status must be one of: {allowed}")
        return v

    model_config = ConfigDict(extra="forbid")


class Appointment(AppointmentBase):
    """
    Complete appointment model with all fields including ID and timestamps

    This is returned from database queries.
    """

    id: int = Field(..., description="Auto-incrementing appointment ID")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "agent_id": "agent_24464697",
                "property_address": "123 Main St, Norman, OK 73069",
                "start_time": "2025-10-10T14:00:00Z",
                "end_time": "2025-10-10T14:30:00Z",
                "attendee_name": "John Doe",
                "attendee_email": "john@example.com",
                "status": "confirmed",
                "vapi_call_id": "call_abc123",
                "calendar_event_id": "AAMkAGI2...",
                "created_at": "2025-10-09T19:00:00Z",
            }
        },
    )

    def dict_for_db(self) -> dict:
        """Convert to dict suitable for database insertion"""
        return {
            "id": self.id if hasattr(self, "id") else None,
            "agent_id": self.agent_id,
            "property_address": self.property_address,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "attendee_name": self.attendee_name,
            "attendee_email": self.attendee_email,
            "status": self.status,
            "vapi_call_id": self.vapi_call_id,
            "calendar_event_id": self.calendar_event_id,
            "created_at": self.created_at,
        }
