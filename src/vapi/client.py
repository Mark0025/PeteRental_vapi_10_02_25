#!/usr/bin/env python3
"""
VAPI Client Wrapper - Programmatic access to VAPI API
Uses official vapi-server-sdk for agent management
"""

import os
from typing import List, Dict, Any, Optional
from loguru import logger
from vapi import Vapi


class VAPIClient:
    """
    Wrapper around VAPI SDK for agent management

    Features:
    - List all agents in VAPI account
    - Create new agents programmatically
    - Update existing agents
    - Delete agents
    - Get agent details
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize VAPI client

        Args:
            api_key: VAPI API key (defaults to VAPI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("VAPI_API_KEY")

        if not self.api_key:
            raise ValueError("VAPI_API_KEY not found in environment variables")

        self.client = Vapi(api_key=self.api_key)
        logger.info("✅ VAPI Client initialized")

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all assistants in VAPI account

        Returns:
            List of agent dictionaries with id, name, model, etc.
        """
        try:
            response = self.client.assistants.list()

            # Convert to list of dicts for easier handling
            agents = []
            for agent in response:
                agents.append({
                    "id": agent.id,
                    "name": getattr(agent, "name", "Unnamed"),
                    "model": getattr(agent, "model", {}),
                    "voice": getattr(agent, "voice", {}),
                    "created_at": getattr(agent, "created_at", None),
                    "updated_at": getattr(agent, "updated_at", None),
                })

            logger.info(f"📋 Found {len(agents)} agents in VAPI account")
            return agents

        except Exception as e:
            logger.error(f"❌ Failed to list agents: {e}")
            raise

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get details for a specific agent

        Args:
            agent_id: VAPI assistant ID

        Returns:
            Agent details dictionary
        """
        try:
            agent = self.client.assistants.get(id=agent_id)

            return {
                "id": agent.id,
                "name": getattr(agent, "name", "Unnamed"),
                "model": getattr(agent, "model", {}),
                "voice": getattr(agent, "voice", {}),
                "server_url": getattr(agent, "server_url", None),
                "first_message": getattr(agent, "first_message", None),
                "created_at": getattr(agent, "created_at", None),
                "updated_at": getattr(agent, "updated_at", None),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get agent {agent_id}: {e}")
            raise

    def create_agent(
        self,
        name: str,
        model: str = "gpt-4o",
        voice_id: str = "elliot",
        server_url: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new VAPI agent

        Args:
            name: Agent name
            model: LLM model (default: gpt-4o)
            voice_id: Voice ID (default: elliot)
            server_url: Webhook URL for custom functions
            **kwargs: Additional agent configuration

        Returns:
            Created agent details
        """
        try:
            # Build agent configuration
            config = {
                "name": name,
                "model": {"model": model},
                "voice": {"voiceId": voice_id},
            }

            if server_url:
                config["serverUrl"] = server_url

            # Merge any additional config
            config.update(kwargs)

            agent = self.client.assistants.create(**config)

            logger.info(f"✅ Created agent: {agent.id} ({name})")

            return {
                "id": agent.id,
                "name": getattr(agent, "name", name),
                "model": getattr(agent, "model", {}),
                "voice": getattr(agent, "voice", {}),
            }

        except Exception as e:
            logger.error(f"❌ Failed to create agent: {e}")
            raise

    def update_agent(self, agent_id: str, **updates) -> Dict[str, Any]:
        """
        Update an existing agent

        Args:
            agent_id: VAPI assistant ID
            **updates: Fields to update

        Returns:
            Updated agent details
        """
        try:
            agent = self.client.assistants.update(id=agent_id, **updates)

            logger.info(f"✅ Updated agent: {agent_id}")

            return {
                "id": agent.id,
                "name": getattr(agent, "name", "Unnamed"),
                "updated_at": getattr(agent, "updated_at", None),
            }

        except Exception as e:
            logger.error(f"❌ Failed to update agent {agent_id}: {e}")
            raise

    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent

        Args:
            agent_id: VAPI assistant ID

        Returns:
            True if deleted successfully
        """
        try:
            self.client.assistants.delete(id=agent_id)
            logger.info(f"🗑️ Deleted agent: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to delete agent {agent_id}: {e}")
            raise


# Singleton instance for easy import
def get_vapi_client() -> VAPIClient:
    """Get or create VAPI client instance"""
    return VAPIClient()
