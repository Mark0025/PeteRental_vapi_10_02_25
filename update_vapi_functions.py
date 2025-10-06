#!/usr/bin/env python3
"""
Update VAPI functions with corrected response template
Fixes: {{output.result.response}} → {{output.result}}
"""

import os
import json
import requests
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_BASE_URL = "https://api.vapi.ai"

if not VAPI_API_KEY:
    logger.error("❌ VAPI_API_KEY not found in .env")
    exit(1)

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

def list_tools():
    """List all tools to find our calendar functions"""
    response = requests.get(f"{VAPI_BASE_URL}/tool", headers=headers)
    response.raise_for_status()
    return response.json()

def update_function(tool_id: str, tool_config: dict):
    """Update a specific function"""
    response = requests.patch(
        f"{VAPI_BASE_URL}/tool/{tool_id}",
        headers=headers,
        json=tool_config
    )
    response.raise_for_status()
    return response.json()

def create_function(tool_config: dict):
    """Create a new function"""
    response = requests.post(
        f"{VAPI_BASE_URL}/tool",
        headers=headers,
        json=tool_config
    )
    response.raise_for_status()
    return response.json()

def main():
    logger.info("🔍 Fetching existing VAPI tools...")

    try:
        tools = list_tools()
        logger.info(f"Found {len(tools)} tools")

        # Load our corrected function definitions
        with open("vapi_calendar_functions.json", "r") as f:
            function_defs = json.load(f)

        # Map of function names to find/update
        function_names = ["get_availability", "set_appointment"]

        for func_def in function_defs["functions"]:
            func_name = func_def["function"]["name"]

            # Find existing tool with this name
            existing_tool = None
            for tool in tools:
                if tool.get("type") == "function":
                    if tool.get("function", {}).get("name") == func_name:
                        existing_tool = tool
                        break

            if existing_tool:
                logger.info(f"📝 Updating existing function: {func_name} (ID: {existing_tool['id']})")
                updated = update_function(existing_tool["id"], func_def)
                logger.info(f"✅ Updated {func_name}")
            else:
                logger.info(f"➕ Creating new function: {func_name}")
                created = create_function(func_def)
                logger.info(f"✅ Created {func_name} (ID: {created['id']})")

        logger.info("\n" + "="*80)
        logger.info("🎉 VAPI functions updated successfully!")
        logger.info("="*80)
        logger.info("\n📋 Next steps:")
        logger.info("1. Go to https://dashboard.vapi.ai → Assistants")
        logger.info("2. Select your assistant")
        logger.info("3. Go to 'Tools' tab")
        logger.info("4. Make sure 'get_availability' and 'set_appointment' are attached")
        logger.info("5. Click 'Publish' to save changes")

    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP Error: {e}")
        logger.error(f"Response: {e.response.text}")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
