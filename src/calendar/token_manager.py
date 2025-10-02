#!/usr/bin/env python3
"""
Token Manager - Reuses rental_database.py pattern for consistency
Stores Microsoft OAuth tokens with same JSON structure
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger
from pathlib import Path


class TokenManager:
    """Manage calendar OAuth tokens - mirrors RentalDatabase structure"""

    def __init__(self, db_file: str = "data/calendar_tokens.json"):
        self.db_file = db_file
        self.ensure_db_exists()

    def ensure_db_exists(self):
        """Create database file if doesn't exist"""
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
        """Load data from JSON file"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Token database issue: {e}, creating new")
            return {"last_updated": None, "tokens": {}, "metadata": {"total_users": 0}}

    def save_data(self, data: Dict[str, Any]):
        """Save data to JSON file"""
        try:
            data["last_updated"] = datetime.now().isoformat()
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Failed to save tokens: {e}")

    def store_token(self, user_id: str, token_data: Dict[str, Any]):
        """Store or update user token"""
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
        logger.info(f"💾 {action} token for user: {user_id}")

    def get_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user token with expiry check"""
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
        data = self.load_data()
        if user_id in data["tokens"]:
            del data["tokens"][user_id]
            data["metadata"]["total_users"] = len(data["tokens"])
            self.save_data(data)
            logger.info(f"🗑️ Deleted token for: {user_id}")

    def get_all_users(self) -> list:
        """Get all user IDs with tokens"""
        data = self.load_data()
        return list(data["tokens"].keys())
