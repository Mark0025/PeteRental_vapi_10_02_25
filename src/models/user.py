"""
User Data Models

Pydantic models for user accounts with Microsoft OAuth integration.
Supports multi-user calendar access and VAPI agent assignment.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base user model with common fields"""

    email: EmailStr = Field(..., description="User email address (login identifier)")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    is_active: bool = Field(default=True, description="Whether user account is active")


class UserCreate(UserBase):
    """
    Model for creating a new user

    Example:
        ```python
        user = UserCreate(
            email="mark@peterei.com",
            full_name="Mark Carpenter"
        )
        ```
    """

    pass


class UserUpdate(BaseModel):
    """
    Model for updating an existing user
    All fields are optional to support partial updates
    """

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class MicrosoftTokenUpdate(BaseModel):
    """
    Model for updating Microsoft OAuth tokens

    Used when storing/refreshing Microsoft Calendar tokens.
    """

    microsoft_access_token: str = Field(..., description="Microsoft OAuth access token")
    microsoft_refresh_token: str = Field(
        ..., description="Microsoft OAuth refresh token"
    )
    microsoft_token_expires_at: datetime = Field(
        ..., description="When access token expires (UTC)"
    )
    microsoft_user_id: Optional[str] = Field(
        None, max_length=255, description="Microsoft user ID"
    )


class User(UserBase):
    """
    Complete user model with all fields including OAuth tokens

    This is returned from database queries and includes sensitive data.
    Use UserPublic for API responses to clients.
    """

    user_id: int = Field(..., description="Auto-incrementing user ID")

    # Microsoft OAuth tokens (sensitive data)
    microsoft_access_token: Optional[str] = Field(
        None, description="Microsoft OAuth access token"
    )
    microsoft_refresh_token: Optional[str] = Field(
        None, description="Microsoft OAuth refresh token"
    )
    microsoft_token_expires_at: Optional[datetime] = Field(
        None, description="When access token expires"
    )
    microsoft_user_id: Optional[str] = Field(None, description="Microsoft user ID")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 1,
                "email": "mark@peterei.com",
                "full_name": "Mark Carpenter",
                "microsoft_access_token": "eyJ0eXAiOiJKV1...",
                "microsoft_refresh_token": "0.AX0A...",
                "microsoft_token_expires_at": "2025-10-09T20:00:00Z",
                "microsoft_user_id": "abc123...",
                "is_active": True,
                "created_at": "2025-10-09T19:00:00Z",
                "updated_at": "2025-10-09T19:00:00Z",
            }
        },
    )


class UserPublic(BaseModel):
    """
    Public user model for API responses

    Excludes sensitive OAuth tokens and internal IDs.
    Safe to return to frontend/external APIs.
    """

    user_id: int
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    has_microsoft_calendar: bool = Field(
        ..., description="Whether user has connected Microsoft Calendar"
    )
    microsoft_token_expires_at: Optional[datetime] = Field(
        None, description="When Microsoft token expires (for UI display)"
    )
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 1,
                "email": "mark@peterei.com",
                "full_name": "Mark Carpenter",
                "is_active": True,
                "has_microsoft_calendar": True,
                "microsoft_token_expires_at": "2025-10-09T20:00:00Z",
                "created_at": "2025-10-09T19:00:00Z",
            }
        },
    )

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        """
        Convert User model to UserPublic (remove sensitive data)

        Args:
            user: Full user model with tokens

        Returns:
            UserPublic with sensitive data removed
        """
        return cls(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            has_microsoft_calendar=bool(user.microsoft_access_token),
            microsoft_token_expires_at=user.microsoft_token_expires_at,
            created_at=user.created_at,
        )


class UserWithAgents(UserPublic):
    """
    User model with assigned VAPI agents

    Used for dashboard/settings pages where user
    needs to see their linked agents.
    """

    agent_count: int = Field(0, description="Number of assigned VAPI agents")
    agents: list = Field(
        default_factory=list, description="List of assigned agents (simplified)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "email": "mark@peterei.com",
                "full_name": "Mark Carpenter",
                "is_active": True,
                "has_microsoft_calendar": True,
                "microsoft_token_expires_at": "2025-10-09T20:00:00Z",
                "created_at": "2025-10-09T19:00:00Z",
                "agent_count": 2,
                "agents": [
                    {
                        "agent_id": "agent_24464697",
                        "agent_name": "Property Manager 1",
                        "is_active": True,
                    },
                    {
                        "agent_id": "agent_98765432",
                        "agent_name": "Rental Assistant",
                        "is_active": True,
                    },
                ],
            }
        }
    )
