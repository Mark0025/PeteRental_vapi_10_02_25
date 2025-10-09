"""
Migration Runner Script

This script runs database migrations on application startup.
Designed to be called from main.py or deployment scripts.

Usage:
    python run_migrations.py

Or integrate into FastAPI startup:
    from src.database import run_migrations

    @app.on_event("startup")
    async def startup():
        await run_migrations()
"""

import asyncio
import sys
from loguru import logger
from src.database import get_database, run_migrations


async def main():
    """Run migrations and exit"""

    logger.info("🚀 Starting database migration runner...")

    try:
        # Connect to database
        db = await get_database()
        logger.info("✅ Database connected")

        # Run migrations
        count = await run_migrations(db)

        if count > 0:
            logger.info(f"✅ Successfully applied {count} new migrations")
        else:
            logger.info("✅ Database is up to date (no new migrations)")

        # Disconnect
        await db.disconnect()
        logger.info("🔌 Database disconnected")

        return 0

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
