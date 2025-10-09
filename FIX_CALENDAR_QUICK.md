# Fix Calendar in Production - Quick Guide

## The Problem (Simple)
Your calendar login gets deleted every time Render redeploys because files don't persist.

## The Fix (5 Steps - 10 Minutes)

### Step 1: Add PostgreSQL to Render
1. Go to Render dashboard: https://dashboard.render.com
2. Click your `peterental-vapi` service
3. Click "Environment" tab
4. Scroll down to "Add-ons"
5. Click "Add PostgreSQL"
6. Select "Starter" plan (free)
7. Click "Create Database"
8. Copy the "Internal Database URL" that appears

### Step 2: Add Database URL to Environment
1. Still in Render dashboard
2. Go to "Environment" tab
3. Click "Add Environment Variable"
4. Key: `DATABASE_URL`
5. Value: [paste the Internal Database URL from step 1]
6. Click "Save"

### Step 3: Update token_manager.py
Replace `src/calendar/token_manager.py` with this simpler version that uses PostgreSQL:

```python
import os
import json
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import Json

class TokenManager:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL")
        if self.db_url:
            # Render gives us postgres://, but psycopg2 needs postgresql://
            if self.db_url.startswith("postgres://"):
                self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)
            self._init_db()
    
    def _init_db(self):
        """Create tokens table if it doesn't exist"""
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                user_id VARCHAR(255) PRIMARY KEY,
                token_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
    
    def store_token(self, user_id: str, token_data: dict):
        """Store OAuth token in PostgreSQL"""
        if not self.db_url:
            print("⚠️ No DATABASE_URL - tokens won't persist!")
            return
        
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO oauth_tokens (user_id, token_data, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_id) 
            DO UPDATE SET token_data = %s, updated_at = NOW()
        ''', (user_id, Json(token_data), Json(token_data)))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Token saved to database for {user_id}")
    
    def get_token(self, user_id: str) -> dict:
        """Get OAuth token from PostgreSQL"""
        if not self.db_url:
            print("⚠️ No DATABASE_URL - can't get token")
            return None
        
        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute('SELECT token_data FROM oauth_tokens WHERE user_id = %s', (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            token_data = result[0]
            # Check if expired
            if 'expires_at' in token_data:
                expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
                if expires_at < datetime.now(expires_at.tzinfo):
                    token_data['is_expired'] = True
            return token_data
        return None
```

### Step 4: Add psycopg2 to dependencies
Add to `pyproject.toml`:
```toml
dependencies = [
    # ... existing deps ...
    "psycopg2-binary>=2.9.0",
]
```

Then run:
```bash
uv sync
```

### Step 5: Deploy and Authorize
```bash
# Commit changes
git add .
git commit -m "Fix: Use PostgreSQL for token storage"
git push origin main

# Render will auto-deploy (watch logs in dashboard)

# Once deployed, visit:
https://peterentalvapi-latest.onrender.com/calendar/setup

# Click "Connect Microsoft Calendar"
# Login with Microsoft
# Done! Token now persists forever
```

## Test It Works
```bash
# Check token is saved
curl "https://peterentalvapi-latest.onrender.com/calendar/auth/status?user_id=pete_admin"
# Should return: {"authorized":true}

# Test calendar function
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "toolCalls": [{
        "function": {
          "name": "get_availability",
          "arguments": {"user_id": "pete_admin", "property_address": "123 Main St"}
        }
      }]
    }
  }'
# Should return available time slots
```

## Why This Works
- PostgreSQL database persists across deploys
- Token saved in database, not in files
- Works for 1 user or 20,000 users
- Free tier includes 1GB database (plenty for tokens)

---

**Total Time:** 10 minutes
**Cost:** $0 (Render free tier includes PostgreSQL starter)
**Result:** Calendar works in production ✅
