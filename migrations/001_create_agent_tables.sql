-- Migration 001: Create Agent and Appointment Tables
-- Purpose: Multi-agent architecture support for VAPI integration
-- Created: 2025-10-09
--
-- This migration creates:
-- 1. agents table - Track all VAPI agents
-- 2. appointments table - Track appointments by agent
-- 3. schema_migrations table - Track applied migrations

-- =============================================================================
-- AGENTS TABLE
-- =============================================================================
-- Stores metadata for each VAPI voice agent
-- Links agents to their VAPI assistant IDs and calendar users

CREATE TABLE IF NOT EXISTS agents (
    -- Internal identifier (human-readable)
    agent_id VARCHAR(255) PRIMARY KEY,

    -- VAPI platform assistant ID (UUID from VAPI)
    vapi_assistant_id VARCHAR(255) UNIQUE NOT NULL,

    -- Human-readable agent name
    agent_name VARCHAR(255) NOT NULL,

    -- Linked calendar user (email) for this agent
    -- NULL if agent doesn't have calendar access yet
    calendar_user_id VARCHAR(255),

    -- Whether agent is active (soft delete support)
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT agent_name_not_empty CHECK (LENGTH(agent_name) > 0),
    CONSTRAINT vapi_id_valid CHECK (LENGTH(vapi_assistant_id) = 36)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_vapi_id ON agents(vapi_assistant_id);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);
CREATE INDEX IF NOT EXISTS idx_agents_calendar_user ON agents(calendar_user_id);

-- Comments for documentation
COMMENT ON TABLE agents IS 'VAPI voice agents with calendar integration';
COMMENT ON COLUMN agents.agent_id IS 'Internal ID (e.g., agent_24464697)';
COMMENT ON COLUMN agents.vapi_assistant_id IS 'VAPI platform UUID';
COMMENT ON COLUMN agents.calendar_user_id IS 'Microsoft Calendar user email';

-- =============================================================================
-- APPOINTMENTS TABLE
-- =============================================================================
-- Stores property viewing appointments
-- Links appointments to the agent who handled them

CREATE TABLE IF NOT EXISTS appointments (
    -- Auto-incrementing primary key
    id SERIAL PRIMARY KEY,

    -- Which agent handled this appointment
    agent_id VARCHAR(255) NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,

    -- VAPI call ID that created this appointment (for tracking)
    vapi_call_id VARCHAR(255),

    -- Appointment details
    property_address TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,

    -- Attendee information
    attendee_name VARCHAR(255) NOT NULL,
    attendee_email VARCHAR(255),

    -- Appointment status
    status VARCHAR(50) DEFAULT 'confirmed' NOT NULL,

    -- Microsoft Calendar event ID (for sync)
    calendar_event_id VARCHAR(255),

    -- Creation timestamp
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('confirmed', 'cancelled', 'completed', 'no_show')),
    CONSTRAINT end_after_start CHECK (end_time > start_time),
    CONSTRAINT property_address_not_empty CHECK (LENGTH(property_address) > 0),
    CONSTRAINT attendee_name_not_empty CHECK (LENGTH(attendee_name) > 0)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_appointments_agent ON appointments(agent_id);
CREATE INDEX IF NOT EXISTS idx_appointments_start_time ON appointments(start_time);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_vapi_call ON appointments(vapi_call_id);
CREATE INDEX IF NOT EXISTS idx_appointments_calendar_event ON appointments(calendar_event_id);

-- Composite indexes for agent analytics
CREATE INDEX IF NOT EXISTS idx_appointments_agent_status ON appointments(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_appointments_agent_date ON appointments(agent_id, start_time);

-- Comments
COMMENT ON TABLE appointments IS 'Property viewing appointments linked to agents';
COMMENT ON COLUMN appointments.agent_id IS 'Agent who handled this appointment';
COMMENT ON COLUMN appointments.vapi_call_id IS 'VAPI call that created appointment';
COMMENT ON COLUMN appointments.calendar_event_id IS 'Microsoft Calendar event ID';

-- =============================================================================
-- MIGRATION TRACKING TABLE
-- =============================================================================
-- Tracks which migrations have been applied
-- Prevents duplicate migration runs

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW() NOT NULL,
    description TEXT
);

COMMENT ON TABLE schema_migrations IS 'Tracks applied database migrations';

-- =============================================================================
-- RECORD THIS MIGRATION
-- =============================================================================
-- Mark migration 001 as applied
INSERT INTO schema_migrations (version, description)
VALUES (1, 'Create agents and appointments tables')
ON CONFLICT (version) DO NOTHING;

-- =============================================================================
-- SAMPLE DATA (Optional - for testing)
-- =============================================================================
-- Uncomment to populate with existing agent
-- INSERT INTO agents (agent_id, vapi_assistant_id, agent_name, calendar_user_id)
-- VALUES (
--     'agent_24464697',
--     '24464697-8f45-4b38-b43a-d337f50c370e',
--     'Appointemt setter agent',
--     'mark@peterei.com'
-- ) ON CONFLICT DO NOTHING;
