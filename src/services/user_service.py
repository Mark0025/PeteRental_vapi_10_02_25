"""
User Service

Business logic layer for user management and Microsoft OAuth integration.
Orchestrates user, agent, and token operations with business rules.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

from src.database import Database
from src.models import (
    User,
    UserCreate,
    UserUpdate,
    UserPublic,
    UserWithAgents,
    MicrosoftTokenUpdate,
)
from src.repositories import UserRepository, AgentRepository


class UserService:
    """
    Service for user management and business operations

    Provides high-level operations for user accounts, OAuth,
    and agent assignment with business rule enforcement.

    Usage:
        ```python
        from src.database import get_database
        from src.services import UserService

        db = await get_database()
        service = UserService(db)

        # Register/get user
        user = await service.get_or_create_user("mark@peterei.com")

        # Store Microsoft tokens
        await service.store_microsoft_tokens(
            "mark@peterei.com",
            access_token="...",
            refresh_token="...",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        # Link agent to user
        await service.link_agent_to_user("agent_24464697", user.user_id)
        ```
    """

    def __init__(self, database: Database):
        """
        Initialize service

        Args:
            database: Database instance
        """
        self.db = database
        self.user_repo = UserRepository(database)
        self.agent_repo = AgentRepository(database)

    async def register_user(
        self, email: str, full_name: Optional[str] = None
    ) -> User:
        """
        Register a new user in the system

        Business logic:
        - Check if user already exists (raise error if exists)
        - Validate email format (done by Pydantic)
        - Create user with proper defaults

        Args:
            email: User email address
            full_name: Optional full name

        Returns:
            Created user

        Raises:
            ValueError: If user already exists
            Exception: If creation fails

        Example:
            ```python
            user = await service.register_user(
                email="mark@peterei.com",
                full_name="Mark Carpenter"
            )
            ```
        """
        # Check if user already exists
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise ValueError(f"User already registered: {email}")

        # Create user
        user_data = UserCreate(email=email, full_name=full_name, is_active=True)

        user = await self.user_repo.create(user_data)
        logger.info(f"🎉 Registered new user: {user.email}")
        return user

    async def get_or_create_user(
        self, email: str, full_name: Optional[str] = None
    ) -> User:
        """
        Get existing user or create new one

        This is the recommended method for user lookup/creation
        as it handles both cases gracefully.

        Args:
            email: User email address
            full_name: Optional full name (used only if creating)

        Returns:
            Existing or newly created user

        Example:
            ```python
            # Idempotent - safe to call multiple times
            user = await service.get_or_create_user("mark@peterei.com")
            ```
        """
        user = await self.user_repo.get_by_email(email)

        if user:
            logger.info(f"👤 Found existing user: {email}")
            return user

        # Create new user
        logger.info(f"✨ Creating new user: {email}")
        user_data = UserCreate(email=email, full_name=full_name, is_active=True)
        return await self.user_repo.create(user_data)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        return await self.user_repo.get_by_email(email)

    async def get_user_public(self, email: str) -> Optional[UserPublic]:
        """
        Get public user data (excludes sensitive tokens)

        Safe for returning to frontend/external APIs.

        Args:
            email: User email

        Returns:
            UserPublic if found, None otherwise
        """
        user = await self.user_repo.get_by_email(email)
        if user:
            return UserPublic.from_user(user)
        return None

    async def get_user_with_agents(self, email: str) -> Optional[UserWithAgents]:
        """
        Get user with their assigned VAPI agents

        Useful for settings/dashboard pages.

        Args:
            email: User email

        Returns:
            UserWithAgents if found, None otherwise

        Example:
            ```python
            user = await service.get_user_with_agents("mark@peterei.com")
            if user:
                print(f"{user.email} has {user.agent_count} agents")
                for agent in user.agents:
                    print(f"  - {agent['agent_name']}")
            ```
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None

        # Get user's agents
        agents = await self.agent_repo.get_by_calendar_user(email)

        # Convert to public user
        user_public = UserPublic.from_user(user)

        # Add agents
        return UserWithAgents(
            **user_public.model_dump(),
            agent_count=len(agents),
            agents=[
                {
                    "agent_id": a.agent_id,
                    "agent_name": a.agent_name,
                    "vapi_assistant_id": a.vapi_assistant_id,
                    "is_active": a.is_active,
                }
                for a in agents
            ],
        )

    async def store_microsoft_tokens(
        self,
        email: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime,
        microsoft_user_id: Optional[str] = None,
    ) -> User:
        """
        Store Microsoft OAuth tokens for a user

        Business logic:
        - Get or create user if doesn't exist
        - Store tokens securely in database
        - Log token expiration

        Args:
            email: User email
            access_token: Microsoft access token
            refresh_token: Microsoft refresh token
            expires_at: When access token expires
            microsoft_user_id: Optional Microsoft user ID

        Returns:
            Updated user

        Example:
            ```python
            from datetime import timedelta

            user = await service.store_microsoft_tokens(
                email="mark@peterei.com",
                access_token="eyJ0eXAi...",
                refresh_token="0.AX0A...",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                microsoft_user_id="abc123..."
            )
            ```
        """
        # Get or create user
        user = await self.get_or_create_user(email)

        # Store tokens
        token_data = MicrosoftTokenUpdate(
            microsoft_access_token=access_token,
            microsoft_refresh_token=refresh_token,
            microsoft_token_expires_at=expires_at,
            microsoft_user_id=microsoft_user_id,
        )

        updated_user = await self.user_repo.update_microsoft_tokens(
            user.user_id, token_data
        )

        if updated_user:
            logger.info(
                f"🔐 Stored Microsoft tokens for {email} "
                f"(expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')})"
            )
            return updated_user

        raise Exception(f"Failed to store Microsoft tokens for {email}")

    async def get_user_calendar_token(self, email: str) -> Optional[str]:
        """
        Get user's Microsoft Calendar access token

        Returns None if user doesn't exist or doesn't have valid token.

        Args:
            email: User email

        Returns:
            Access token if valid, None otherwise
        """
        user = await self.user_repo.get_by_email(email)

        if not user or not user.microsoft_access_token:
            return None

        # Check if token is expired
        if user.microsoft_token_expires_at and user.microsoft_token_expires_at < datetime.utcnow():
            logger.warning(f"⏰ Token expired for {email}")
            return None

        return user.microsoft_access_token

    async def has_valid_calendar_access(self, email: str) -> bool:
        """
        Check if user has valid Microsoft Calendar access

        Args:
            email: User email

        Returns:
            True if has valid access, False otherwise
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return False

        return await self.user_repo.has_valid_microsoft_token(user.user_id)

    async def disconnect_microsoft_calendar(self, email: str) -> bool:
        """
        Disconnect user's Microsoft Calendar (clear tokens)

        Args:
            email: User email

        Returns:
            True if successful, False if user not found
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            return False

        cleared = await self.user_repo.clear_microsoft_tokens(user.user_id)
        if cleared:
            logger.info(f"🔓 Disconnected Microsoft Calendar for {email}")
            return True
        return False

    async def link_agent_to_user(self, agent_id: str, user_id: int) -> bool:
        """
        Link a VAPI agent to a user

        Business logic:
        - Verify agent exists
        - Verify user exists
        - Update agent.user_id

        Args:
            agent_id: Agent to link
            user_id: User to link to

        Returns:
            True if successful, False if agent/user not found

        Example:
            ```python
            success = await service.link_agent_to_user(
                "agent_24464697",
                user_id=1
            )
            ```
        """
        # Verify user exists
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"❌ User not found: {user_id}")
            return False

        # Verify agent exists
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            logger.error(f"❌ Agent not found: {agent_id}")
            return False

        # Link agent to user (update agent's user_id)
        from src.models import AgentUpdate

        updated = await self.agent_repo.update(agent_id, AgentUpdate(user_id=user_id))

        if updated:
            logger.info(f"🔗 Linked agent {agent.agent_name} to user {user.email}")
            return True

        return False

    async def get_user_agents(self, email: str) -> List[Any]:
        """
        Get all agents assigned to a user

        Args:
            email: User email

        Returns:
            List of agents (may be empty)
        """
        return await self.agent_repo.get_by_calendar_user(email)

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system-wide user statistics

        Returns:
            Dictionary with user stats

        Example:
            ```python
            stats = await service.get_system_stats()
            # {
            #     "users": {"total": 10, "active": 8, "with_calendar": 6},
            #     "agents": {"total": 12, "assigned": 10}
            # }
            ```
        """
        total_users = await self.user_repo.count_all()
        active_users = await self.user_repo.count_active()
        users_with_calendar = await self.user_repo.count_with_microsoft_calendar()

        total_agents = await self.agent_repo.count_all()
        active_agents = await self.agent_repo.count_active()

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "with_calendar": users_with_calendar,
            },
            "agents": {"total": total_agents, "active": active_agents},
        }
