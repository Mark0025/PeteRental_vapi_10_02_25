#!/usr/bin/env python3
"""
Verify VAPI Assistant Configuration on Startup
Checks that tools are properly configured and accessible
"""

import requests
import os
import sys
from datetime import datetime

VAPI_API_KEY = "d180ee70-5c20-4d9a-af4f-97f9e1d8957d"
ASSISTANT_ID = "24464697-8f45-4b38-b43a-d337f50c370e"

def check_assistant_config():
    """Verify assistant has tools configured correctly"""

    print("=" * 80)
    print("🔍 VAPI Assistant Configuration Check")
    print("=" * 80)

    # Get assistant configuration
    url = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"
    headers = {"Authorization": f"Bearer {VAPI_API_KEY}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        assistant = response.json()

        print(f"\n✅ Assistant Found: {assistant['name']}")
        print(f"📅 Last Updated: {assistant['updatedAt']}")
        print(f"🤖 Model: {assistant['model']['model']}")

        # Check tools
        tools = assistant['model'].get('tools', [])

        if not tools:
            print("\n❌ ERROR: No tools configured!")
            return False

        print(f"\n📦 Tools Configured: {len(tools)}")

        for i, tool in enumerate(tools, 1):
            tool_name = tool['function']['name']
            server_url = tool['server']['url']
            timeout = tool['server']['timeoutSeconds']
            is_async = tool.get('async', False)

            print(f"\n🔧 Tool {i}: {tool_name}")
            print(f"   URL: {server_url}")
            print(f"   Timeout: {timeout}s")
            print(f"   Async: {is_async}")

            # Check messages
            messages = tool.get('messages', [])
            for msg in messages:
                if msg['type'] == 'request-start':
                    blocking = msg.get('blocking', False)
                    print(f"   Blocking: {blocking}")

                    if not blocking:
                        print(f"   ⚠️  WARNING: blocking is False! Tool will not wait for response.")

            # Check if URL is accessible
            try:
                health_check = requests.get(f"{server_url.replace('/vapi/webhook', '/health')}", timeout=5)
                if health_check.status_code == 200:
                    print(f"   ✅ Webhook server is reachable")
                else:
                    print(f"   ⚠️  Webhook server returned {health_check.status_code}")
            except Exception as e:
                print(f"   ❌ Webhook server unreachable: {e}")

        print("\n" + "=" * 80)
        print("✅ Configuration check complete!")
        print("=" * 80)
        return True

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        print(f"Status Code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_assistant_config()
    sys.exit(0 if success else 1)
