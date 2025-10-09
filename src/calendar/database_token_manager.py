"""
Database Token Manager (New)

Uses the new users table and UserService for token management.
Replaces the old oauth_tokens table approach with proper async operations.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from src.services import UserService
from src.database import get_database


class DatabaseTokenManager:
    """
    Modern token manager using UserService and async database operations

    Usage:
        ```python
        from src.calendar.database_token_manager import get_token_manager

        # Get singleton instance
        manager = await get_token_manager()

        # Store tokens
        await manager.store_token(
            user_id="mark@peterei.com",
            token_data={
                "access_token": "...",
                "refresh_token": "...",
                "expires_at": datetime(...),
            }
        )

        # Get tokens
        token = await manager.get_token("mark@peterei.com")
        ```
    """

    def __init__(self, user_service: UserService):
        """
        Initialize token manager

        Args:
            user_service: UserService instance for token operations
        """
        self.user_service = user_service
        logger.info("✅ DatabaseTokenManager initialized (using users table)")

    async def store_token(self, user_id: str, token_data: Dict[str, Any]) -> bool:
        """
        Store or update user's Microsoft OAuth token

        Args:
            user_id: User email address
            token_data: Dictionary containing:
                - access_token: Microsoft access token
                - refresh_token: Microsoft refresh token
                - expires_at: datetime or ISO string
                - microsoft_user_id: Optional Microsoft user ID

        Returns:
            True if successful

        Example:
            ```python
            from datetime import datetime, timedelta

            success = await manager.store_token(
                user_id="mark@peterei.com",
                token_data={
                    "access_token": "eyJ0eXAi...",
                    "refresh_token": "0.AX0A...",
                    "expires_at": datetime.utcnow() + timedelta(hours=1),
                    "microsoft_user_id": "abc123..."
                }
            )
            ```
        """
        try:
            # Parse expires_at
            expires_at = token_data["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(
                    expires_at.replace("Z", "+00:00")
                )

            # Store tokens via UserService
            await self.user_service.store_microsoft_tokens(
                email=user_id,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", ""),
                expires_at=expires_at,
                microsoft_user_id=token_data.get("microsoft_user_id"),
            )

            logger.info(
                f"💾 [Database] Stored token for: {user_id} "
                f"(expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')})"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to store token for {user_id}: {e}")
            return False

    async def get_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's Microsoft OAuth token with expiry check

        Args:
            user_id: User email address

        Returns:
            Dictionary with token data or None if not found:
                - user_id: User email
                - access_token: Microsoft access token
                - refresh_token: Microsoft refresh token
                - expires_at: ISO string
                - is_expired: Boolean
                - microsoft_user_id: Microsoft user ID

        Example:
            ```python
            token = await manager.get_token("mark@peterei.com")
            if token and not token["is_expired"]:
                # Use token.access_token
                pass
            ```
        """
        try:
            # Get user via UserService
            user = await self.user_service.get_user_by_email(user_id)

            if not user or not user.microsoft_access_token:
                logger.debug(f"No token found for: {user_id}")
                return None

            # Check expiry
            is_expired = False
            if user.microsoft_token_expires_at:
                is_expired = user.microsoft_token_expires_at < datetime.utcnow()

            return {
                "user_id": user.email,
                "access_token": user.microsoft_access_token,
                "refresh_token": user.microsoft_refresh_token or "",
                "expires_at": user.microsoft_token_expires_at.isoformat()
                if user.microsoft_token_expires_at
                else None,
                "is_expired": is_expired,
                "microsoft_user_id": user.microsoft_user_id,
                "calendar_email": user.email,  # For backward compatibility
            }

        except Exception as e:
            logger.error(f"❌ Failed to get token for {user_id}: {e}")
            return None

    async def delete_token(self, user_id: str) -> bool:
        """
        Delete user's Microsoft OAuth tokens

        Args:
            user_id: User email address

        Returns:
            True if successful
        """
        try:
            success = await self.user_service.disconnect_microsoft_calendar(user_id)

            if success:
                logger.info(f"🗑️  [Database] Deleted token for: {user_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Failed to delete token for {user_id}: {e}")
            return False

    async def get_all_users(self) -> list:
        """
        Get all user IDs (emails) with stored tokens

        Returns:
            List of user email addresses
        """
        try:
            # This could be optimized with a specific query,
            # but for now we'll use the existing service methods
            users = await self.user_service.user_repo.list_active()

            # Filter to only users with Microsoft tokens
            return [
                user.email
                for user in users
                if user.microsoft_access_token is not None
            ]

        except Exception as e:
            logger.error(f"❌ Failed to get all users: {e}")
            return []


# Global singleton instance
_token_manager: Optional[DatabaseTokenManager] = None


async def get_token_manager() -> DatabaseTokenManager:
    """
    Get or create global DatabaseTokenManager instance

    This ensures a single token manager across the application.

    Returns:
        DatabaseTokenManager: Initialized token manager

    Usage:
        ```python
        from src.calendar.database_token_manager import get_token_manager

        manager = await get_token_manager()
        token = await manager.get_token("mark@peterei.com")
        ```
    """
    global _token_manager

    if _token_manager is None:
        db = await get_database()
        user_service = UserService(db)
        _token_manager = DatabaseTokenManager(user_service)

    return _token_manager


def get_token_manager_sync() -> DatabaseTokenManager:
    """
    Synchronous wrapper for getting token manager

    Uses asyncio.run() to create manager if needed.
    Useful for backward compatibility with sync code.

    Returns:
        DatabaseTokenManager: Token manager instance

    Note:
        Prefer using async get_token_manager() when possible.
        This is for backward compatibility only.
    """
    global _token_manager

    if _token_manager is None:
        # Create new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        _token_manager = loop.run_until_complete(get_token_manager())

    return _token_manager
