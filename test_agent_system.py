"""
Agent System Integration Test

Tests the complete multi-agent architecture:
- Database connection
- Pydantic models
- Repositories (data access)
- Services (business logic)

This demonstrates how the clean architecture works together.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from loguru import logger

from src.database import get_database
from src.services import AgentService
from src.models import AgentCreate, AppointmentCreate


async def test_agent_registration():
    """Test registering a new agent"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Agent Registration")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        # Register a test agent
        agent = await service.register_agent(
            vapi_assistant_id="12345678-1234-1234-1234-123456789012",
            agent_name="Test Property Manager",
            calendar_user_id="test@peterei.com",
        )

        logger.info(f"✅ Registered agent: {agent.agent_id}")
        logger.info(f"   Name: {agent.agent_name}")
        logger.info(f"   VAPI ID: {agent.vapi_assistant_id}")
        logger.info(f"   Calendar User: {agent.calendar_user_id}")
        logger.info(f"   Active: {agent.is_active}")

        # Try to register same agent again (should fail)
        try:
            await service.register_agent(
                vapi_assistant_id="12345678-1234-1234-1234-123456789012",
                agent_name="Duplicate Agent",
            )
            logger.error("❌ Duplicate registration should have failed!")
            return False
        except ValueError as e:
            logger.info(f"✅ Duplicate registration correctly rejected: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_agent_lookup():
    """Test looking up agents"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Agent Lookup")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        # Lookup by VAPI ID (primary method for webhooks)
        agent = await service.get_agent_by_vapi_id(
            "12345678-1234-1234-1234-123456789012"
        )

        if agent:
            logger.info(f"✅ Found agent by VAPI ID: {agent.agent_name}")
        else:
            logger.error("❌ Agent not found by VAPI ID")
            return False

        # Get agent with stats
        agent_info = await service.get_agent_with_stats(agent.agent_id)

        if agent_info:
            logger.info(f"✅ Retrieved agent with stats:")
            logger.info(f"   Total appointments: {agent_info['stats']['total']}")
            logger.info(f"   Confirmed: {agent_info['stats']['confirmed']}")
            logger.info(f"   Completed: {agent_info['stats']['completed']}")
        else:
            logger.error("❌ Failed to get agent with stats")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_appointment_creation():
    """Test creating appointments"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Appointment Creation")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        # Get agent
        agent = await service.get_agent_by_vapi_id(
            "12345678-1234-1234-1234-123456789012"
        )

        if not agent:
            logger.error("❌ Agent not found")
            return False

        # Create appointment
        start_time = datetime.now(timezone.utc) + timedelta(days=1, hours=14)
        end_time = start_time + timedelta(minutes=30)

        appointment = await service.create_appointment(
            agent_id=agent.agent_id,
            property_address="123 Main St, Norman, OK 73069",
            start_time=start_time,
            end_time=end_time,
            attendee_name="John Doe",
            attendee_email="john@example.com",
            vapi_call_id="test_call_123",
        )

        logger.info(f"✅ Created appointment #{appointment.id}")
        logger.info(f"   Property: {appointment.property_address}")
        logger.info(f"   Attendee: {appointment.attendee_name}")
        logger.info(f"   Start: {appointment.start_time}")
        logger.info(f"   Status: {appointment.status}")
        logger.info(f"   VAPI Call: {appointment.vapi_call_id}")

        # Create another appointment
        start_time2 = datetime.now(timezone.utc) + timedelta(days=2, hours=10)
        end_time2 = start_time2 + timedelta(minutes=30)

        appointment2 = await service.create_appointment(
            agent_id=agent.agent_id,
            property_address="456 Oak Ave, Norman, OK 73072",
            start_time=start_time2,
            end_time=end_time2,
            attendee_name="Jane Smith",
            attendee_email="jane@example.com",
        )

        logger.info(f"✅ Created second appointment #{appointment2.id}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_appointment_queries():
    """Test querying appointments"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Appointment Queries")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        # Get agent
        agent = await service.get_agent_by_vapi_id(
            "12345678-1234-1234-1234-123456789012"
        )

        if not agent:
            logger.error("❌ Agent not found")
            return False

        # Get all appointments for agent
        appointments = await service.get_agent_appointments(agent.agent_id)
        logger.info(f"✅ Found {len(appointments)} total appointments for agent")

        # Get confirmed appointments
        confirmed = await service.get_agent_appointments(
            agent.agent_id, status="confirmed"
        )
        logger.info(f"✅ Found {len(confirmed)} confirmed appointments")

        # Get upcoming appointments
        upcoming = await service.get_upcoming_appointments(agent.agent_id)
        logger.info(f"✅ Found {len(upcoming)} upcoming appointments")

        for appt in upcoming:
            logger.info(f"   - {appt.attendee_name} at {appt.property_address}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_agent_stats():
    """Test agent statistics"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Agent Statistics")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        # Get agent
        agent = await service.get_agent_by_vapi_id(
            "12345678-1234-1234-1234-123456789012"
        )

        if not agent:
            logger.error("❌ Agent not found")
            return False

        # Get agent with stats
        agent_info = await service.get_agent_with_stats(agent.agent_id)

        logger.info(f"✅ Agent Statistics for {agent.agent_name}:")
        logger.info(f"   Total appointments: {agent_info['stats']['total']}")
        logger.info(f"   Confirmed: {agent_info['stats']['confirmed']}")
        logger.info(f"   Completed: {agent_info['stats']['completed']}")
        logger.info(f"   Cancelled: {agent_info['stats']['cancelled']}")
        logger.info(f"   No-show: {agent_info['stats']['no_show']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_system_stats():
    """Test system-wide statistics"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: System Statistics")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        stats = await service.get_system_stats()

        logger.info("✅ System-Wide Statistics:")
        logger.info(f"   Total agents: {stats['agents']['total']}")
        logger.info(f"   Active agents: {stats['agents']['active']}")
        logger.info(f"   Total appointments: {stats['appointments']['total']}")
        logger.info(f"   By status:")
        logger.info(f"      Confirmed: {stats['appointments']['by_status']['confirmed']}")
        logger.info(f"      Completed: {stats['appointments']['by_status']['completed']}")
        logger.info(f"      Cancelled: {stats['appointments']['by_status']['cancelled']}")
        logger.info(f"      No-show: {stats['appointments']['by_status']['no_show']}")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def test_agent_deactivation():
    """Test agent deactivation"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 7: Agent Deactivation")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        # Get agent
        agent = await service.get_agent_by_vapi_id(
            "12345678-1234-1234-1234-123456789012"
        )

        if not agent:
            logger.error("❌ Agent not found")
            return False

        # Deactivate agent
        success = await service.deactivate_agent(agent.agent_id)
        if success:
            logger.info(f"✅ Deactivated agent: {agent.agent_name}")
        else:
            logger.error("❌ Failed to deactivate agent")
            return False

        # Verify agent is inactive
        updated_agent = await service.get_agent_by_vapi_id(agent.vapi_assistant_id)
        if not updated_agent.is_active:
            logger.info("✅ Agent is now inactive")
        else:
            logger.error("❌ Agent should be inactive")
            return False

        # Reactivate agent
        success = await service.reactivate_agent(agent.agent_id)
        if success:
            logger.info(f"✅ Reactivated agent: {agent.agent_name}")
        else:
            logger.error("❌ Failed to reactivate agent")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


async def cleanup():
    """Clean up test data"""
    logger.info("\n" + "=" * 70)
    logger.info("CLEANUP: Removing test data")
    logger.info("=" * 70)

    db = await get_database()
    service = AgentService(db)

    try:
        # Get test agent
        agent = await service.get_agent_by_vapi_id(
            "12345678-1234-1234-1234-123456789012"
        )

        if agent:
            # Delete agent (cascades to appointments)
            success = await service.agent_repo.delete(agent.agent_id)
            if success:
                logger.info(f"✅ Cleaned up test agent and appointments")
            else:
                logger.warning("⚠️  Test agent not found for cleanup")

        await db.disconnect()
        return True

    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("=" * 70)
    logger.info("🧪 AGENT SYSTEM INTEGRATION TEST")
    logger.info("=" * 70)

    # Only run tests if DATABASE_URL is set
    import os

    if not os.getenv("DATABASE_URL"):
        logger.warning("⏭️  Skipping tests (DATABASE_URL not set)")
        logger.info("Tests will run automatically on Render deployment")
        return True

    try:
        tests = [
            ("Agent Registration", test_agent_registration),
            ("Agent Lookup", test_agent_lookup),
            ("Appointment Creation", test_appointment_creation),
            ("Appointment Queries", test_appointment_queries),
            ("Agent Statistics", test_agent_stats),
            ("System Statistics", test_system_stats),
            ("Agent Deactivation", test_agent_deactivation),
        ]

        results = []
        for name, test_func in tests:
            try:
                result = await test_func()
                results.append((name, result))
            except Exception as e:
                logger.error(f"❌ {name} crashed: {e}")
                results.append((name, False))

        # Cleanup
        await cleanup()

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 70)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {name}")

        logger.info(f"\n🎯 {passed}/{total} tests passed")

        if passed == total:
            logger.info("=" * 70)
            logger.info("🎉 ALL TESTS PASSED - System is working correctly!")
            logger.info("=" * 70)
            return True
        else:
            logger.warning("=" * 70)
            logger.warning("⚠️  SOME TESTS FAILED - Review errors above")
            logger.warning("=" * 70)
            return False

    except Exception as e:
        logger.error(f"\n❌ TEST SUITE FAILED: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
