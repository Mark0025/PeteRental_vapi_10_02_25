-- Migration 002: Add User Authentication and Multi-User Support
-- Purpose: Enable multiple users with Microsoft Calendar OAuth integration
-- Created: 2025-10-09
--
-- This migration creates:
-- 1. users table - User accounts with OAuth tokens
-- 2. Links agents to users
-- 3. Enables multi-user calendar access

-- =============================================================================
-- USERS TABLE
-- =============================================================================
-- Stores user accounts with Microsoft OAuth integration
-- Each user can have multiple VAPI agents assigned to them

CREATE TABLE IF NOT EXISTS users (
    -- Auto-incrementing primary key
    user_id SERIAL PRIMARY KEY,

    -- User identification
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),

    -- Microsoft OAuth tokens (stored securely)
    -- Access token for API calls (expires in ~1 hour)
    microsoft_access_token TEXT,

    -- Refresh token for getting new access tokens (long-lived)
    microsoft_refresh_token TEXT,

    -- When the current access token expires
    microsoft_token_expires_at TIMESTAMP,

    -- User profile info from Microsoft
    microsoft_user_id VARCHAR(255),

    -- User status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT email_valid CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_microsoft_id ON users(microsoft_user_id);

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts with Microsoft Calendar OAuth integration';
COMMENT ON COLUMN users.email IS 'User email address (login identifier)';
COMMENT ON COLUMN users.microsoft_access_token IS 'Microsoft OAuth access token (encrypted)';
COMMENT ON COLUMN users.microsoft_refresh_token IS 'Microsoft OAuth refresh token (encrypted)';
COMMENT ON COLUMN users.microsoft_token_expires_at IS 'When access token expires (UTC)';

-- =============================================================================
-- LINK AGENTS TO USERS
-- =============================================================================
-- Add user_id foreign key to agents table
-- This allows multiple agents per user

ALTER TABLE agents
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

-- Index for user lookup
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);

-- Comment
COMMENT ON COLUMN agents.user_id IS 'User who owns/manages this agent';

-- =============================================================================
-- MIGRATION DATA: Migrate existing calendar_user_id to users table
-- =============================================================================
-- For existing agents with calendar_user_id set, create users and link them
-- This ensures backward compatibility

-- Insert unique calendar users as new user accounts
INSERT INTO users (email, is_active)
SELECT DISTINCT calendar_user_id, TRUE
FROM agents
WHERE calendar_user_id IS NOT NULL
  AND calendar_user_id NOT IN (SELECT email FROM users)
ON CONFLICT (email) DO NOTHING;

-- Link existing agents to their users
UPDATE agents
SET user_id = users.user_id
FROM users
WHERE agents.calendar_user_id = users.email
  AND agents.user_id IS NULL;

-- =============================================================================
-- RECORD THIS MIGRATION
-- =============================================================================
-- Mark migration 002 as applied
INSERT INTO schema_migrations (version, description)
VALUES (2, 'Add user authentication and link agents to users')
ON CONFLICT (version) DO NOTHING;

-- =============================================================================
-- NOTES FOR DEVELOPERS
-- =============================================================================
-- After this migration:
--
-- 1. New user flow:
--    - User signs up → row in users table
--    - User connects Microsoft → tokens stored in users table
--    - User assigns VAPI agent → agents.user_id = users.user_id
--
-- 2. VAPI webhook flow:
--    - Get agent by vapi_assistant_id
--    - Get user via agents.user_id
--    - Use user.microsoft_access_token for calendar operations
--
-- 3. Backward compatibility:
--    - agents.calendar_user_id still exists (can be deprecated later)
--    - Existing agents automatically linked to users
--    - Token migration from file to database happens in application code
--
-- 4. Security:
--    - Tokens stored in database (consider encryption at rest)
--    - Access tokens expire and auto-refresh
--    - User can revoke access via Microsoft
