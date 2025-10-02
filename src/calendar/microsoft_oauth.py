#!/usr/bin/env python3
"""
Microsoft OAuth Handler - Production-ready OAuth 2.0 flow
Uses MSAL for Microsoft authentication
"""

from msal import ConfidentialClientApplication
from typing import Dict
import os
from datetime import datetime, timedelta
from loguru import logger


class MicrosoftOAuth:
    """Handle Microsoft OAuth 2.0 for calendar access"""

    def __init__(self):
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
        self.redirect_uri = os.getenv(
            "MICROSOFT_REDIRECT_URI",
            "https://peterentalvapi-latest.onrender.com/calendar/auth/callback"
        )

        # Validate required config
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️ Microsoft OAuth credentials not configured")

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["Calendars.ReadWrite", "User.Read"]

        if self.client_id and self.client_secret:
            self.app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
        else:
            self.app = None

    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        if not self.app:
            raise Exception("OAuth not configured - missing credentials")

        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=state
        )
        logger.info(f"🔗 Generated auth URL with state: {state[:10]}...")
        return auth_url

    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        if not self.app:
            raise Exception("OAuth not configured")

        result = self.app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )

        if "error" in result:
            error_msg = result.get('error_description', result.get('error'))
            logger.error(f"❌ Token exchange failed: {error_msg}")
            raise Exception(f"Token exchange failed: {error_msg}")

        logger.info("✅ Successfully exchanged code for token")

        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),
            "expires_at": datetime.now() + timedelta(seconds=result["expires_in"]),
            "token_type": result["token_type"],
            "scope": " ".join(result.get("scope", []))
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh expired access token"""
        if not self.app:
            raise Exception("OAuth not configured")

        result = self.app.acquire_token_by_refresh_token(
            refresh_token=refresh_token,
            scopes=self.scopes
        )

        if "error" in result:
            error_msg = result.get('error_description', result.get('error'))
            logger.error(f"❌ Token refresh failed: {error_msg}")
            raise Exception(f"Token refresh failed: {error_msg}")

        logger.info("✅ Successfully refreshed token")

        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", refresh_token),  # Keep old if not provided
            "expires_at": datetime.now() + timedelta(seconds=result["expires_in"])
        }
