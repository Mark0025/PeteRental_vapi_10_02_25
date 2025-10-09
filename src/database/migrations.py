"""
Database Migration Runner

Automatically applies SQL migrations in version order.
Tracks applied migrations to ensure idempotent operation.
"""

import os
from pathlib import Path
from typing import List, Tuple
from loguru import logger
from .connection import Database


class MigrationRunner:
    """
    Manages database schema migrations

    Usage:
        ```python
        from src.database import get_database, run_migrations

        db = await get_database()
        await run_migrations(db)
        ```
    """

    def __init__(self, database: Database, migrations_dir: str = "migrations"):
        """
        Initialize migration runner

        Args:
            database: Database instance
            migrations_dir: Directory containing migration SQL files
        """
        self.db = database
        self.migrations_dir = Path(migrations_dir)

        if not self.migrations_dir.exists():
            raise ValueError(f"Migrations directory not found: {self.migrations_dir}")

    async def get_applied_migrations(self) -> List[int]:
        """
        Get list of already applied migration versions

        Returns:
            List of migration version numbers
        """
        try:
            # Check if schema_migrations table exists
            table_exists = await self.db.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'schema_migrations'
                )
                """
            )

            if not table_exists:
                logger.info("📋 schema_migrations table doesn't exist yet (first run)")
                return []

            # Get all applied migrations
            rows = await self.db.fetch(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
            versions = [row["version"] for row in rows]
            logger.info(f"✅ Found {len(versions)} applied migrations: {versions}")
            return versions

        except Exception as e:
            logger.warning(f"⚠️  Could not read applied migrations: {e}")
            return []

    def get_migration_files(self) -> List[Tuple[int, Path]]:
        """
        Get all migration files sorted by version number

        Returns:
            List of (version, filepath) tuples

        Migration files must follow pattern: {version}_{description}.sql
        Example: 001_create_agent_tables.sql
        """
        migrations = []

        for file_path in self.migrations_dir.glob("*.sql"):
            try:
                # Extract version number from filename (e.g., "001_create_agent_tables.sql" -> 1)
                version_str = file_path.stem.split("_")[0]
                version = int(version_str)
                migrations.append((version, file_path))
            except (ValueError, IndexError) as e:
                logger.warning(f"⚠️  Skipping invalid migration file: {file_path.name} ({e})")
                continue

        # Sort by version number
        migrations.sort(key=lambda x: x[0])
        logger.info(f"📁 Found {len(migrations)} migration files")
        return migrations

    async def apply_migration(self, version: int, file_path: Path) -> None:
        """
        Apply a single migration file

        Args:
            version: Migration version number
            file_path: Path to SQL migration file

        Raises:
            Exception: If migration fails
        """
        logger.info(f"🔄 Applying migration {version}: {file_path.name}")

        try:
            # Read migration SQL
            sql = file_path.read_text()

            # Execute migration
            async with self.db.acquire() as conn:
                # Run the migration SQL
                await conn.execute(sql)
                logger.info(f"✅ Migration {version} applied successfully")

        except Exception as e:
            logger.error(f"❌ Migration {version} failed: {e}")
            raise

    async def run_migrations(self) -> int:
        """
        Apply all pending migrations in order

        This method is idempotent - safe to run multiple times.
        Only unapplied migrations will be executed.

        Returns:
            Number of migrations applied

        Raises:
            Exception: If any migration fails
        """
        logger.info("🚀 Starting migration check...")

        # Get applied migrations
        applied = await self.get_applied_migrations()

        # Get all migration files
        all_migrations = self.get_migration_files()

        if not all_migrations:
            logger.warning("⚠️  No migration files found")
            return 0

        # Find pending migrations
        pending = [
            (version, path)
            for version, path in all_migrations
            if version not in applied
        ]

        if not pending:
            logger.info("✅ All migrations already applied - database is up to date")
            return 0

        logger.info(f"📝 Found {len(pending)} pending migrations")

        # Apply each pending migration
        applied_count = 0
        for version, file_path in pending:
            await self.apply_migration(version, file_path)
            applied_count += 1

        logger.info(f"🎉 Successfully applied {applied_count} migrations")
        return applied_count


async def run_migrations(database: Database = None, migrations_dir: str = "migrations") -> int:
    """
    Convenience function to run all pending migrations

    Args:
        database: Database instance (will create one if not provided)
        migrations_dir: Directory containing migration files

    Returns:
        Number of migrations applied

    Usage:
        ```python
        # With existing database
        from src.database import get_database, run_migrations

        db = await get_database()
        count = await run_migrations(db)
        print(f"Applied {count} migrations")

        # Standalone
        from src.database import run_migrations
        count = await run_migrations()
        ```
    """
    if database is None:
        from .connection import get_database
        database = await get_database()

    runner = MigrationRunner(database, migrations_dir)
    return await runner.run_migrations()
