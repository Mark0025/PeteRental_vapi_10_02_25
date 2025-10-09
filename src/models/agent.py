"""
Agent Data Models

Pydantic models for VAPI agent representation with validation.
Supports create/read/update operations with proper type safety.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class AgentBase(BaseModel):
    """Base agent model with common fields"""

    agent_name: str = Field(
        ..., min_length=1, max_length=255, description="Human-readable agent name"
    )
    vapi_assistant_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="VAPI platform assistant ID (UUID)",
    )
    calendar_user_id: Optional[str] = Field(
        None, max_length=255, description="Linked calendar user ID (email)"
    )
    is_active: bool = Field(default=True, description="Whether agent is active")

    @field_validator("vapi_assistant_id")
    @classmethod
    def validate_vapi_id(cls, v: str) -> str:
        """Ensure VAPI ID looks like a valid UUID"""
        if len(v) != 36 or v.count("-") != 4:
            raise ValueError("vapi_assistant_id must be a valid UUID")
        return v


class AgentCreate(AgentBase):
    """
    Model for creating a new agent

    Example:
        ```python
        agent = AgentCreate(
            agent_name="Property Manager 1",
            vapi_assistant_id="24464697-8f45-4b38-b43a-d337f50c370e",
            calendar_user_id="mark@peterei.com"
        )
        ```
    """

    pass


class AgentUpdate(BaseModel):
    """
    Model for updating an existing agent
    All fields are optional to support partial updates
    """

    agent_name: Optional[str] = Field(None, min_length=1, max_length=255)
    calendar_user_id: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")  # Prevent unknown fields


class Agent(AgentBase):
    """
    Complete agent model with all fields including timestamps

    This is returned from database queries and includes metadata.
    """

    agent_id: str = Field(..., description="Internal agent identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM mode
        json_schema_extra={
            "example": {
                "agent_id": "agent_24464697",
                "agent_name": "Appointemt setter agent",
                "vapi_assistant_id": "24464697-8f45-4b38-b43a-d337f50c370e",
                "calendar_user_id": "mark@peterei.com",
                "is_active": True,
                "created_at": "2025-10-09T19:00:00Z",
                "updated_at": "2025-10-09T19:00:00Z",
            }
        },
    )

    def dict_for_db(self) -> dict:
        """Convert to dict suitable for database insertion"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "vapi_assistant_id": self.vapi_assistant_id,
            "calendar_user_id": self.calendar_user_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
