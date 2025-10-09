# Database Migration Guide

**Purpose:** Version-controlled database schema changes for multi-agent architecture

## 📋 Overview

Database migrations provide:
- **Version Control** - Track schema changes like Git for code
- **Idempotency** - Safe to run multiple times (no duplicate changes)
- **Rollback Safety** - Track what's been applied, what hasn't
- **Team Collaboration** - Everyone gets the same schema
- **Production Safety** - Automatic deployment with zero downtime

## 🏗️ Architecture

### Components

```
migrations/                         # Migration SQL files
├── 001_create_agent_tables.sql    # Initial schema
└── 002_add_user_auth.sql          # Future migration

src/database/
├── connection.py                   # Async connection pool
├── migrations.py                   # Migration runner
└── __init__.py                     # Exports

run_migrations.py                   # CLI runner script
test_migrations.py                  # Test suite
```

### Database Schema

```sql
-- Migration tracking table (auto-created)
schema_migrations
  ├── version (INTEGER PRIMARY KEY)
  ├── applied_at (TIMESTAMP)
  └── description (TEXT)

-- Multi-agent support (Migration 001)
agents
  ├── agent_id (VARCHAR PRIMARY KEY)
  ├── vapi_assistant_id (VARCHAR UNIQUE)
  ├── agent_name (VARCHAR)
  ├── calendar_user_id (VARCHAR)
  ├── is_active (BOOLEAN)
  ├── created_at (TIMESTAMP)
  └── updated_at (TIMESTAMP)

appointments
  ├── id (SERIAL PRIMARY KEY)
  ├── agent_id (VARCHAR FK → agents.agent_id)
  ├── vapi_call_id (VARCHAR)
  ├── property_address (TEXT)
  ├── start_time (TIMESTAMP)
  ├── end_time (TIMESTAMP)
  ├── attendee_name (VARCHAR)
  ├── attendee_email (VARCHAR)
  ├── status (VARCHAR CHECK)
  ├── calendar_event_id (VARCHAR)
  └── created_at (TIMESTAMP)
```

## 🚀 Running Migrations

### On Render (Production)

Migrations run automatically on deployment via the startup script:

1. **Build Phase** - Docker container built with all migration files
2. **Start Phase** - `run_migrations.py` executes before FastAPI starts
3. **Verification** - Logs show migration status

**Check Logs:**
```bash
# In Render dashboard, check deployment logs for:
✅ Database connected
✅ Successfully applied 1 new migrations
# OR
✅ Database is up to date (no new migrations)
```

### Manual Execution

If you have DATABASE_URL configured locally:

```bash
# Run all pending migrations
python run_migrations.py

# Or integrate into FastAPI startup
# (See main.py @app.on_event("startup"))
```

### Testing (with DATABASE_URL)

```bash
# Comprehensive migration test suite
python test_migrations.py

# Expected output:
✅ Database connected
✅ Applied 1 migrations
✅ All tables verified
✅ Indexes verified
✅ Migration tracking verified
✅ Idempotency verified
```

## 📝 Creating New Migrations

### Step 1: Create Migration File

```bash
# Naming convention: {version}_{description}.sql
touch migrations/002_add_user_authentication.sql
```

### Step 2: Write SQL

```sql
-- Migration 002: Add User Authentication
-- Purpose: Support multiple users with email/password auth
-- Created: 2025-10-09

-- =============================================================================
-- USERS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    CONSTRAINT email_valid CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Link agents to users
ALTER TABLE agents
ADD COLUMN user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_agents_user ON agents(user_id);

-- =============================================================================
-- RECORD THIS MIGRATION
-- =============================================================================

INSERT INTO schema_migrations (version, description)
VALUES (2, 'Add user authentication and link to agents')
ON CONFLICT (version) DO NOTHING;
```

### Step 3: Test Migration

```bash
# Test on local database (if available)
python test_migrations.py

# Or deploy to Render staging environment
git push origin feature/your-branch
```

### Step 4: Commit

```bash
git add migrations/002_add_user_authentication.sql
git commit -m "feat: Add user authentication migration"
```

## 🔧 Migration Best Practices

### ✅ DO

- **Use `IF NOT EXISTS`** - Makes migrations idempotent
- **Add indexes** - Optimize query performance
- **Add constraints** - Enforce data integrity at database level
- **Add comments** - Document purpose and creation date
- **Test locally first** - If you have DATABASE_URL
- **Use CHECK constraints** - Validate data (email format, status enums, etc.)
- **Record migration** - Always insert into `schema_migrations` table

### ❌ DON'T

- **Don't modify existing migrations** - Create new ones instead
- **Don't skip version numbers** - Keep sequential (001, 002, 003...)
- **Don't drop tables without backup** - Use soft deletes (is_active flag)
- **Don't forget foreign keys** - Maintain referential integrity
- **Don't forget to test** - Broken migrations break deployments

## 🐛 Troubleshooting

### Migration Fails on Render

**Check Render logs:**
```
❌ Migration 2 failed: relation "users" already exists
```

**Fix:** Migration is not idempotent. Add `IF NOT EXISTS`:
```sql
CREATE TABLE IF NOT EXISTS users (...)
```

### Migration Applied But Tables Missing

**Check database:**
```python
from src.database import get_database
db = await get_database()
tables = await db.fetch("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
""")
print(tables)
```

**Fix:** Verify migration was actually applied:
```sql
SELECT * FROM schema_migrations;
```

### Can't Test Locally

**Issue:** No DATABASE_URL in .env

**Solutions:**
1. **Use Render database** - Test on staging deployment
2. **Set up local PostgreSQL:**
   ```bash
   # Install PostgreSQL
   brew install postgresql@14  # macOS

   # Start service
   brew services start postgresql@14

   # Create database
   createdb peterental_dev

   # Add to .env
   DATABASE_URL=postgresql://localhost/peterental_dev
   ```
3. **Use Docker:**
   ```bash
   docker run -d \
     --name postgres-dev \
     -e POSTGRES_DB=peterental_dev \
     -e POSTGRES_PASSWORD=dev \
     -p 5432:5432 \
     postgres:14

   # Add to .env
   DATABASE_URL=postgresql://postgres:dev@localhost:5432/peterental_dev
   ```

## 📊 Migration Status

### Check Applied Migrations

```python
from src.database import get_database

db = await get_database()
migrations = await db.fetch("""
    SELECT version, applied_at, description
    FROM schema_migrations
    ORDER BY version
""")

for m in migrations:
    print(f"✅ Migration {m['version']}: {m['description']} ({m['applied_at']})")
```

### Check Pending Migrations

```python
from src.database.migrations import MigrationRunner

runner = MigrationRunner(db)
applied = await runner.get_applied_migrations()
all_files = runner.get_migration_files()
pending = [v for v, _ in all_files if v not in applied]

print(f"Applied: {applied}")
print(f"Pending: {pending}")
```

## 🔐 Security Notes

- **Never commit DATABASE_URL** - It contains credentials
- **Use environment variables** - Keep secrets out of code
- **Validate input** - Use CHECK constraints for data validation
- **Use parameterized queries** - Prevent SQL injection
- **Audit migrations** - Review before deploying to production

## 🎯 Integration with FastAPI

### Automatic Migration on Startup

Add to `main.py`:

```python
from src.database import run_migrations

@app.on_event("startup")
async def startup_migrations():
    """Run database migrations on application startup"""
    try:
        count = await run_migrations()
        if count > 0:
            logger.info(f"✅ Applied {count} new migrations")
        else:
            logger.info("✅ Database up to date")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        # Don't crash the app - allow it to start
        # (migrations might fail if DATABASE_URL not set locally)
```

## 📚 Related Documentation

- [COMPLETE_SYSTEM_ANALYSIS.md](../architecture/COMPLETE_SYSTEM_ANALYSIS.md) - Full system architecture
- [RENDER_DEPLOYMENT.md](../deployment/RENDER_DEPLOYMENT.md) - Production deployment
- [RENDER_ENV_VARS.md](../deployment/RENDER_ENV_VARS.md) - Environment variables

## 🚦 Next Steps

1. **Review Migration 001** - Check `migrations/001_create_agent_tables.sql`
2. **Deploy to Render** - Migrations run automatically
3. **Verify in Logs** - Check for migration success messages
4. **Create Agent Repository** - Implement data access layer
5. **Create Agent Service** - Implement business logic
6. **Update VAPI Webhook** - Use new database schema

---

**Created:** 2025-10-09
**Last Updated:** 2025-10-09
**Status:** ✅ Ready for Production
