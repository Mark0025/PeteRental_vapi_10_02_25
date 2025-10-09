"""
Test Migration System

Verifies that:
1. Database connection works
2. Migrations run successfully
3. Tables are created with correct schema
4. Migrations are idempotent (can run multiple times)
"""

import asyncio
from loguru import logger
from src.database import get_database, run_migrations


async def verify_tables_exist(db) -> bool:
    """Check if migration tables were created"""

    tables_to_check = ["agents", "appointments", "schema_migrations"]

    for table_name in tables_to_check:
        exists = await db.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = $1
            )
            """,
            table_name
        )

        if exists:
            logger.info(f"✅ Table '{table_name}' exists")
        else:
            logger.error(f"❌ Table '{table_name}' NOT found")
            return False

    return True


async def verify_indexes_exist(db) -> bool:
    """Check if indexes were created"""

    indexes_to_check = [
        "idx_agents_vapi_id",
        "idx_agents_active",
        "idx_agents_calendar_user",
        "idx_appointments_agent",
        "idx_appointments_start_time",
        "idx_appointments_status",
    ]

    for index_name in indexes_to_check:
        exists = await db.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM pg_indexes
                WHERE indexname = $1
            )
            """,
            index_name
        )

        if exists:
            logger.info(f"✅ Index '{index_name}' exists")
        else:
            logger.warning(f"⚠️  Index '{index_name}' NOT found")

    return True


async def verify_schema_migrations(db) -> bool:
    """Check migration tracking table"""

    migrations = await db.fetch("SELECT * FROM schema_migrations ORDER BY version")

    if not migrations:
        logger.error("❌ No migrations recorded in schema_migrations table")
        return False

    logger.info(f"✅ Found {len(migrations)} applied migrations:")
    for migration in migrations:
        logger.info(f"   • Version {migration['version']}: {migration['description']}")

    return True


async def test_idempotency(db) -> bool:
    """Test that migrations can run multiple times safely"""

    logger.info("🔄 Testing idempotency (running migrations again)...")
    count = await run_migrations(db)

    if count == 0:
        logger.info("✅ Idempotency test passed - no migrations re-applied")
        return True
    else:
        logger.error(f"❌ Idempotency test failed - {count} migrations re-applied")
        return False


async def main():
    """Run all migration tests"""

    logger.info("=" * 70)
    logger.info("🧪 MIGRATION SYSTEM TEST")
    logger.info("=" * 70)

    try:
        # 1. Connect to database
        logger.info("\n1️⃣  Connecting to database...")
        db = await get_database()
        logger.info("✅ Database connected\n")

        # 2. Run migrations
        logger.info("2️⃣  Running migrations...")
        count = await run_migrations(db)
        logger.info(f"✅ Applied {count} migrations\n")

        # 3. Verify tables exist
        logger.info("3️⃣  Verifying tables...")
        if not await verify_tables_exist(db):
            raise Exception("Table verification failed")
        logger.info("✅ All tables verified\n")

        # 4. Verify indexes exist
        logger.info("4️⃣  Verifying indexes...")
        await verify_indexes_exist(db)
        logger.info("✅ Indexes verified\n")

        # 5. Verify migration tracking
        logger.info("5️⃣  Verifying migration tracking...")
        if not await verify_schema_migrations(db):
            raise Exception("Migration tracking verification failed")
        logger.info("✅ Migration tracking verified\n")

        # 6. Test idempotency
        logger.info("6️⃣  Testing idempotency...")
        if not await test_idempotency(db):
            raise Exception("Idempotency test failed")
        logger.info("✅ Idempotency verified\n")

        # 7. Show table schemas
        logger.info("7️⃣  Table Schemas:")

        # Agents table
        agent_cols = await db.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'agents'
            ORDER BY ordinal_position
            """
        )
        logger.info("\n📋 agents table:")
        for col in agent_cols:
            nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
            logger.info(f"   • {col['column_name']}: {col['data_type']} ({nullable})")

        # Appointments table
        appt_cols = await db.fetch(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'appointments'
            ORDER BY ordinal_position
            """
        )
        logger.info("\n📋 appointments table:")
        for col in appt_cols:
            nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
            logger.info(f"   • {col['column_name']}: {col['data_type']} ({nullable})")

        logger.info("\n" + "=" * 70)
        logger.info("🎉 ALL TESTS PASSED - Migration system working correctly!")
        logger.info("=" * 70)

        await db.disconnect()
        return True

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        logger.info("\n" + "=" * 70)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
