#!/usr/bin/env python3
"""
Token Manager - PostgreSQL with File Fallback
Stores Microsoft OAuth tokens in PostgreSQL (production) or JSON files (local dev)
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger
from pathlib import Path


class TokenManager:
    """Manage calendar OAuth tokens - PostgreSQL in production, JSON files locally"""

    def __init__(self, db_file: str = "data/calendar_tokens.json"):
        self.db_file = db_file
        self.db_url = os.getenv("DATABASE_URL")
        self.use_postgres = False

        # Try to use PostgreSQL if available
        if self.db_url:
            try:
                import psycopg2
                # Render gives postgres://, but psycopg2 needs postgresql://
                if self.db_url.startswith("postgres://"):
                    self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)
                self._init_postgres()
                self.use_postgres = True
                logger.info("✅ Using PostgreSQL for token storage (persistent)")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL not available ({e}), falling back to file storage")
                self.use_postgres = False
        else:
            logger.info("💾 Using file storage for tokens (local dev mode)")

        # Ensure file storage exists as fallback
        if not self.use_postgres:
            self.ensure_db_exists()

    def _init_postgres(self):
        """Create tokens table in PostgreSQL if doesn't exist"""
        import psycopg2

        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS oauth_tokens (
                user_id VARCHAR(255) PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                expires_at TIMESTAMP NOT NULL,
                token_type VARCHAR(50) DEFAULT 'Bearer',
                scope TEXT,
                calendar_email VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ PostgreSQL tokens table ready")

    def ensure_db_exists(self):
        """Create database file if doesn't exist (file fallback)"""
        Path(self.db_file).parent.mkdir(parents=True, exist_ok=True)

        if not os.path.exists(self.db_file):
            initial_data = {
                "last_updated": None,
                "tokens": {},
                "metadata": {
                    "total_users": 0,
                    "version": "1.0"
                }
            }
            self.save_data(initial_data)
            logger.info(f"✅ Created token database: {self.db_file}")

    def load_data(self) -> Dict[str, Any]:
        """Load data from JSON file (fallback mode)"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Token database issue: {e}, creating new")
            return {"last_updated": None, "tokens": {}, "metadata": {"total_users": 0}}

    def save_data(self, data: Dict[str, Any]):
        """Save data to JSON file (fallback mode)"""
        try:
            data["last_updated"] = datetime.now().isoformat()
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Failed to save tokens: {e}")

    def store_token(self, user_id: str, token_data: Dict[str, Any]):
        """Store or update user token"""
        if self.use_postgres:
            self._store_token_postgres(user_id, token_data)
        else:
            self._store_token_file(user_id, token_data)

    def _store_token_postgres(self, user_id: str, token_data: Dict[str, Any]):
        """Store token in PostgreSQL"""
        import psycopg2

        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()

        # Convert expires_at to timestamp if needed
        expires_at = token_data["expires_at"]
        if not isinstance(expires_at, str):
            expires_at = expires_at.isoformat()

        cur.execute('''
            INSERT INTO oauth_tokens
            (user_id, access_token, refresh_token, expires_at, token_type, scope, calendar_email, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at,
                token_type = EXCLUDED.token_type,
                scope = EXCLUDED.scope,
                calendar_email = EXCLUDED.calendar_email,
                updated_at = NOW()
        ''', (
            user_id,
            token_data["access_token"],
            token_data.get("refresh_token"),
            expires_at,
            token_data.get("token_type", "Bearer"),
            token_data.get("scope", ""),
            token_data.get("calendar_email", "")
        ))

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"💾 [PostgreSQL] Stored token for user: {user_id}")

    def _store_token_file(self, user_id: str, token_data: Dict[str, Any]):
        """Store token in JSON file (fallback)"""
        data = self.load_data()

        # Check if updating existing token
        is_update = user_id in data["tokens"]
        created_at = data["tokens"].get(user_id, {}).get("created_at", datetime.now().isoformat())

        data["tokens"][user_id] = {
            "user_id": user_id,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": token_data["expires_at"] if isinstance(token_data["expires_at"], str) else token_data["expires_at"].isoformat(),
            "token_type": token_data.get("token_type", "Bearer"),
            "scope": token_data.get("scope", ""),
            "calendar_email": token_data.get("calendar_email", ""),
            "created_at": created_at,
            "updated_at": datetime.now().isoformat()
        }

        data["metadata"]["total_users"] = len(data["tokens"])
        self.save_data(data)

        action = "Updated" if is_update else "Stored"
        logger.info(f"💾 [File] {action} token for user: {user_id}")

    def get_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user token with expiry check"""
        if self.use_postgres:
            return self._get_token_postgres(user_id)
        else:
            return self._get_token_file(user_id)

    def _get_token_postgres(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get token from PostgreSQL"""
        import psycopg2

        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute('''
            SELECT access_token, refresh_token, expires_at, token_type, scope, calendar_email, created_at, updated_at
            FROM oauth_tokens
            WHERE user_id = %s
        ''', (user_id,))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            return None

        token_data = {
            "user_id": user_id,
            "access_token": result[0],
            "refresh_token": result[1],
            "expires_at": result[2].isoformat() if hasattr(result[2], 'isoformat') else str(result[2]),
            "token_type": result[3],
            "scope": result[4],
            "calendar_email": result[5],
            "created_at": result[6].isoformat() if hasattr(result[6], 'isoformat') else str(result[6]),
            "updated_at": result[7].isoformat() if hasattr(result[7], 'isoformat') else str(result[7])
        }

        # Check expiry
        expires_at = datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
        token_data["is_expired"] = datetime.now(expires_at.tzinfo) >= expires_at

        return token_data

    def _get_token_file(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get token from JSON file"""
        data = self.load_data()
        token_data = data["tokens"].get(user_id)

        if not token_data:
            return None

        # Check expiry
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        token_data["is_expired"] = datetime.now() >= expires_at

        return token_data

    def delete_token(self, user_id: str):
        """Delete user token"""
        if self.use_postgres:
            self._delete_token_postgres(user_id)
        else:
            self._delete_token_file(user_id)

    def _delete_token_postgres(self, user_id: str):
        """Delete token from PostgreSQL"""
        import psycopg2

        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute('DELETE FROM oauth_tokens WHERE user_id = %s', (user_id,))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"🗑️ [PostgreSQL] Deleted token for: {user_id}")

    def _delete_token_file(self, user_id: str):
        """Delete token from JSON file"""
        data = self.load_data()
        if user_id in data["tokens"]:
            del data["tokens"][user_id]
            data["metadata"]["total_users"] = len(data["tokens"])
            self.save_data(data)
            logger.info(f"🗑️ [File] Deleted token for: {user_id}")

    def get_all_users(self) -> list:
        """Get all user IDs with tokens"""
        if self.use_postgres:
            return self._get_all_users_postgres()
        else:
            return self._get_all_users_file()

    def _get_all_users_postgres(self) -> list:
        """Get all users from PostgreSQL"""
        import psycopg2

        conn = psycopg2.connect(self.db_url)
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM oauth_tokens')
        users = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return users

    def _get_all_users_file(self) -> list:
        """Get all users from JSON file"""
        data = self.load_data()
        return list(data["tokens"].keys())
