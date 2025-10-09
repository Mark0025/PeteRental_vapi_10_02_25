#!/usr/bin/env python3
"""Attach calendar tools to VAPI assistant"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"
ASSISTANT_ID = "24464697-8f45-4b38-b43a-d337f50c370e"
GET_AVAILABILITY_TOOL_ID = "cec6f21b-8b74-47a6-b73d-633eb9d71930"
SET_APPOINTMENT_TOOL_ID = "0903d34d-6f63-4430-b06e-a908a0056209"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

print("🔗 Attaching calendar tools to assistant...\n")

# Update assistant to include server tools
# Try multiple formats - VAPI API docs show different field names
update_payload = {
    "model": {
        "tools": [
            {
                "type": "function",
                "function": {
                    "toolId": GET_AVAILABILITY_TOOL_ID
                }
            },
            {
                "type": "function",
                "function": {
                    "toolId": SET_APPOINTMENT_TOOL_ID
                }
            }
        ]
    }
}

response = requests.patch(
    f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
    headers=headers,
    json=update_payload
)

if response.status_code in [200, 201]:
    print("✅ Tools attached successfully!")
    assistant = response.json()

    server_tools = assistant.get('serverTools', [])
    print(f"\n🔧 Server Tools Now Attached: {len(server_tools)}")
    for tool in server_tools:
        if isinstance(tool, dict) and 'id' in tool:
            print(f"   - Tool ID: {tool['id']}")

    print("\n🎉 Assistant is now configured with calendar functions!")
    print("📞 Try a voice call now - agent should be able to check availability")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
