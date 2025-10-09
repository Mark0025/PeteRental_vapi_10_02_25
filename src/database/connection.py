"""
Async Database Connection Pool

Manages PostgreSQL connection pooling using asyncpg for high-performance
async database operations. Implements connection lifecycle management.
"""

import os
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg
from loguru import logger


class Database:
    """
    Async PostgreSQL connection pool manager

    Usage:
        ```python
        db = Database(database_url)
        await db.connect()

        async with db.acquire() as conn:
            result = await conn.fetch("SELECT * FROM agents")

        await db.disconnect()
        ```
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection pool

        Args:
            database_url: PostgreSQL connection string
                         Defaults to DATABASE_URL environment variable
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")

        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        # Fix Render's postgres:// to postgresql://
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace(
                "postgres://", "postgresql://", 1
            )

        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self, min_size: int = 10, max_size: int = 20) -> None:
        """
        Establish connection pool

        Args:
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections allowed

        Raises:
            ConnectionError: If unable to connect to database
        """
        if self._pool is not None:
            logger.warning("Database pool already exists")
            return

        try:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=min_size,
                max_size=max_size,
                command_timeout=60,
            )
            logger.info(
                f"✅ Database pool created (min={min_size}, max={max_size} connections)"
            )

            # Test connection
            async with self._pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info(f"📊 Connected to: {version[:50]}...")

        except Exception as e:
            logger.error(f"❌ Failed to create database pool: {e}")
            raise ConnectionError(f"Database connection failed: {e}")

    async def disconnect(self) -> None:
        """Close all connections in the pool"""
        if self._pool is None:
            logger.warning("No pool to disconnect")
            return

        await self._pool.close()
        self._pool = None
        logger.info("🔌 Database pool closed")

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from the pool (context manager)

        Usage:
            ```python
            async with db.acquire() as conn:
                result = await conn.fetch("SELECT * FROM agents")
            ```

        Yields:
            asyncpg.Connection: Database connection

        Raises:
            RuntimeError: If pool not initialized
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")

        async with self._pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args) -> str:
        """
        Execute a query without returning results

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Status message from database

        Example:
            ```python
            await db.execute(
                "INSERT INTO agents (agent_id, agent_name) VALUES ($1, $2)",
                "agent_001", "Property Manager"
            )
            ```
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """
        Fetch multiple rows

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            List of records

        Example:
            ```python
            agents = await db.fetch("SELECT * FROM agents WHERE is_active = $1", True)
            ```
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[dict]:
        """
        Fetch a single row

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single record or None

        Example:
            ```python
            agent = await db.fetchrow(
                "SELECT * FROM agents WHERE agent_id = $1",
                "agent_001"
            )
            ```
        """
        async with self.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetchval(self, query: str, *args):
        """
        Fetch a single value

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single value or None

        Example:
            ```python
            count = await db.fetchval("SELECT COUNT(*) FROM agents")
            ```
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global database instance
_database: Optional[Database] = None


async def get_database() -> Database:
    """
    Get or create global database instance

    This ensures a single connection pool across the application.

    Returns:
        Database: Initialized database instance

    Usage:
        ```python
        from src.database import get_database

        db = await get_database()
        agents = await db.fetch("SELECT * FROM agents")
        ```
    """
    global _database

    if _database is None:
        _database = Database()
        await _database.connect()

    return _database
