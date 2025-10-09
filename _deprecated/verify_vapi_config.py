#!/usr/bin/env python3
"""Verify VAPI tool configuration"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"
VAPI_BASE_URL = "https://api.vapi.ai"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

print("🔍 Checking get_availability tool configuration...\n")

response = requests.get(
    f"{VAPI_BASE_URL}/tool/cec6f21b-8b74-47a6-b73d-633eb9d71930",
    headers=headers
)

if response.status_code == 200:
    tool = response.json()
    print("✅ Tool found!\n")
    print("📋 Current Configuration:")
    print(json.dumps(tool, indent=2))

    # Check the messages template
    if "messages" in tool:
        print("\n🎯 Response Template:")
        for msg in tool["messages"]:
            if msg.get("type") == "request-complete":
                print(f"  Content: {msg.get('content')}")
    else:
        print("\n⚠️  No messages template found!")

    # Check server config
    if "server" in tool:
        print(f"\n🌐 Webhook URL: {tool['server'].get('url')}")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
