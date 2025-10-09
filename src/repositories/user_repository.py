"""
User Repository

Data access layer for user operations.
Handles user CRUD, OAuth token management, and agent linking.
"""

from typing import List, Optional
from datetime import datetime
from loguru import logger

from src.database import Database
from src.models import User, UserCreate, UserUpdate, MicrosoftTokenUpdate


class UserRepository:
    """
    Repository for user database operations

    Usage:
        ```python
        from src.database import get_database
        from src.repositories import UserRepository

        db = await get_database()
        repo = UserRepository(db)

        # Create user
        user = await repo.create(UserCreate(
            email="mark@peterei.com",
            full_name="Mark Carpenter"
        ))

        # Get by email
        user = await repo.get_by_email("mark@peterei.com")

        # Store Microsoft tokens
        await repo.update_microsoft_tokens(
            user.user_id,
            MicrosoftTokenUpdate(...)
        )
        ```
    """

    def __init__(self, database: Database):
        """
        Initialize repository

        Args:
            database: Database instance
        """
        self.db = database

    async def create(self, user_data: UserCreate) -> User:
        """
        Create a new user

        Args:
            user_data: User creation data

        Returns:
            Created user with generated user_id

        Raises:
            Exception: If user with same email exists
        """
        query = """
            INSERT INTO users (email, full_name, is_active)
            VALUES ($1, $2, $3)
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(
                query, user_data.email, user_data.full_name, user_data.is_active
            )

            if not row:
                raise Exception("Failed to create user")

            user = User(**dict(row))
            logger.info(f"✅ Created user: {user.email} (ID: {user.user_id})")
            return user

        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            raise

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        query = "SELECT * FROM users WHERE user_id = $1"
        row = await self.db.fetchrow(query, user_id)

        if row:
            return User(**dict(row))
        return None

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address

        This is the primary lookup method for login/authentication.

        Args:
            email: User email address

        Returns:
            User if found, None otherwise

        Example:
            ```python
            user = await repo.get_by_email("mark@peterei.com")
            if user:
                print(f"Found: {user.full_name}")
            ```
        """
        query = "SELECT * FROM users WHERE LOWER(email) = LOWER($1)"
        row = await self.db.fetchrow(query, email)

        if row:
            return User(**dict(row))
        return None

    async def get_by_microsoft_id(self, microsoft_user_id: str) -> Optional[User]:
        """
        Get user by Microsoft user ID

        Useful for OAuth flows where Microsoft returns their user ID.

        Args:
            microsoft_user_id: Microsoft user identifier

        Returns:
            User if found, None otherwise
        """
        query = "SELECT * FROM users WHERE microsoft_user_id = $1"
        row = await self.db.fetchrow(query, microsoft_user_id)

        if row:
            return User(**dict(row))
        return None

    async def list_active(self) -> List[User]:
        """
        Get all active users

        Returns:
            List of active users ordered by creation date
        """
        query = """
            SELECT * FROM users
            WHERE is_active = TRUE
            ORDER BY created_at DESC
        """
        rows = await self.db.fetch(query)
        return [User(**dict(row)) for row in rows]

    async def list_all(self) -> List[User]:
        """
        Get all users (including inactive)

        Returns:
            List of all users ordered by creation date
        """
        query = "SELECT * FROM users ORDER BY created_at DESC"
        rows = await self.db.fetch(query)
        return [User(**dict(row)) for row in rows]

    async def update(self, user_id: int, update_data: UserUpdate) -> Optional[User]:
        """
        Update user information

        Only updates fields provided in update_data (partial updates supported).

        Args:
            user_id: User to update
            update_data: Fields to update

        Returns:
            Updated user if found, None otherwise

        Example:
            ```python
            updated = await repo.update(
                1,
                UserUpdate(full_name="Mark R. Carpenter")
            )
            ```
        """
        update_fields = update_data.model_dump(exclude_unset=True)

        if not update_fields:
            existing = await self.get_by_id(user_id)
            return existing

        # Always update updated_at timestamp
        update_fields["updated_at"] = datetime.utcnow()

        # Build SET clause
        set_clause = ", ".join(
            f"{field} = ${i + 2}" for i, field in enumerate(update_fields.keys())
        )
        values = [user_id] + list(update_fields.values())

        query = f"""
            UPDATE users
            SET {set_clause}
            WHERE user_id = $1
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(query, *values)

            if not row:
                logger.warning(f"⚠️  User not found: {user_id}")
                return None

            user = User(**dict(row))
            logger.info(f"✅ Updated user: {user.email}")
            return user

        except Exception as e:
            logger.error(f"❌ Failed to update user {user_id}: {e}")
            raise

    async def update_microsoft_tokens(
        self, user_id: int, token_data: MicrosoftTokenUpdate
    ) -> Optional[User]:
        """
        Store Microsoft OAuth tokens for a user

        This is called after successful Microsoft OAuth flow.

        Args:
            user_id: User to update
            token_data: Microsoft OAuth token data

        Returns:
            Updated user if found, None otherwise

        Example:
            ```python
            updated = await repo.update_microsoft_tokens(
                user_id=1,
                token_data=MicrosoftTokenUpdate(
                    microsoft_access_token="eyJ0eXAi...",
                    microsoft_refresh_token="0.AX0A...",
                    microsoft_token_expires_at=datetime.utcnow() + timedelta(hours=1),
                    microsoft_user_id="abc123..."
                )
            )
            ```
        """
        query = """
            UPDATE users
            SET microsoft_access_token = $1,
                microsoft_refresh_token = $2,
                microsoft_token_expires_at = $3,
                microsoft_user_id = $4,
                updated_at = NOW()
            WHERE user_id = $5
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(
                query,
                token_data.microsoft_access_token,
                token_data.microsoft_refresh_token,
                token_data.microsoft_token_expires_at,
                token_data.microsoft_user_id,
                user_id,
            )

            if not row:
                logger.warning(f"⚠️  User not found: {user_id}")
                return None

            user = User(**dict(row))
            logger.info(
                f"✅ Updated Microsoft tokens for: {user.email} "
                f"(expires: {user.microsoft_token_expires_at})"
            )
            return user

        except Exception as e:
            logger.error(f"❌ Failed to update Microsoft tokens for user {user_id}: {e}")
            raise

    async def clear_microsoft_tokens(self, user_id: int) -> Optional[User]:
        """
        Clear Microsoft OAuth tokens (user disconnects calendar)

        Args:
            user_id: User to update

        Returns:
            Updated user if found, None otherwise
        """
        query = """
            UPDATE users
            SET microsoft_access_token = NULL,
                microsoft_refresh_token = NULL,
                microsoft_token_expires_at = NULL,
                microsoft_user_id = NULL,
                updated_at = NOW()
            WHERE user_id = $1
            RETURNING *
        """

        try:
            row = await self.db.fetchrow(query, user_id)

            if not row:
                return None

            user = User(**dict(row))
            logger.info(f"🔓 Cleared Microsoft tokens for: {user.email}")
            return user

        except Exception as e:
            logger.error(f"❌ Failed to clear Microsoft tokens for user {user_id}: {e}")
            raise

    async def has_valid_microsoft_token(self, user_id: int) -> bool:
        """
        Check if user has a valid (non-expired) Microsoft token

        Args:
            user_id: User to check

        Returns:
            True if has valid token, False otherwise
        """
        query = """
            SELECT EXISTS(
                SELECT 1 FROM users
                WHERE user_id = $1
                  AND microsoft_access_token IS NOT NULL
                  AND microsoft_token_expires_at > NOW()
            )
        """
        return await self.db.fetchval(query, user_id)

    async def get_users_needing_token_refresh(self, minutes_before_expiry: int = 5) -> List[User]:
        """
        Get users whose Microsoft tokens are about to expire

        Useful for background token refresh jobs.

        Args:
            minutes_before_expiry: How many minutes before expiry to consider

        Returns:
            List of users needing token refresh
        """
        query = """
            SELECT * FROM users
            WHERE microsoft_access_token IS NOT NULL
              AND microsoft_refresh_token IS NOT NULL
              AND microsoft_token_expires_at IS NOT NULL
              AND microsoft_token_expires_at <= NOW() + ($1 || ' minutes')::INTERVAL
              AND is_active = TRUE
            ORDER BY microsoft_token_expires_at ASC
        """
        rows = await self.db.fetch(query, minutes_before_expiry)
        return [User(**dict(row)) for row in rows]

    async def deactivate(self, user_id: int) -> bool:
        """
        Soft delete user by setting is_active = False

        Preserves user data and agent assignments.

        Args:
            user_id: User to deactivate

        Returns:
            True if deactivated, False if not found
        """
        updated = await self.update(user_id, UserUpdate(is_active=False))
        return updated is not None

    async def activate(self, user_id: int) -> bool:
        """
        Reactivate a deactivated user

        Args:
            user_id: User to activate

        Returns:
            True if activated, False if not found
        """
        updated = await self.update(user_id, UserUpdate(is_active=True))
        return updated is not None

    async def delete(self, user_id: int) -> bool:
        """
        Hard delete user from database

        ⚠️  WARNING: This permanently deletes the user.
        User's agents will have user_id set to NULL (ON DELETE SET NULL).
        Use deactivate() for soft delete instead.

        Args:
            user_id: User to delete

        Returns:
            True if deleted, False if not found
        """
        query = "DELETE FROM users WHERE user_id = $1"

        try:
            result = await self.db.execute(query, user_id)
            deleted = "DELETE 1" in result
            if deleted:
                logger.warning(f"⚠️  HARD DELETED user: {user_id}")
            return deleted

        except Exception as e:
            logger.error(f"❌ Failed to delete user {user_id}: {e}")
            raise

    async def exists(self, email: str) -> bool:
        """
        Check if user exists by email

        Useful for avoiding duplicate accounts.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE LOWER(email) = LOWER($1))"
        return await self.db.fetchval(query, email)

    async def count_active(self) -> int:
        """
        Count active users

        Returns:
            Number of active users
        """
        query = "SELECT COUNT(*) FROM users WHERE is_active = TRUE"
        return await self.db.fetchval(query)

    async def count_all(self) -> int:
        """
        Count all users (including inactive)

        Returns:
            Total number of users
        """
        query = "SELECT COUNT(*) FROM users"
        return await self.db.fetchval(query)

    async def count_with_microsoft_calendar(self) -> int:
        """
        Count users with connected Microsoft Calendar

        Returns:
            Number of users with Microsoft tokens
        """
        query = """
            SELECT COUNT(*) FROM users
            WHERE microsoft_access_token IS NOT NULL
              AND is_active = TRUE
        """
        return await self.db.fetchval(query)
