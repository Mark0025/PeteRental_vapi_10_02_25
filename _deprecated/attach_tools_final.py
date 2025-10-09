#!/usr/bin/env python3
"""Attach calendar tools to VAPI assistant - proper API format"""
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

print("🔍 Fetching current assistant configuration...\n")

# First, GET the full assistant config
response = requests.get(
    f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
    headers=headers
)

if response.status_code != 200:
    print(f"❌ Failed to fetch assistant: {response.status_code}")
    print(response.text)
    exit(1)

assistant = response.json()
print(f"✅ Current assistant: {assistant.get('name')}")

# Now PATCH with the model.tools array
# Based on VAPI API docs: https://docs.vapi.ai/api-reference/assistants/update
print("\n🔗 Attaching calendar tools...\n")

update_payload = {
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "tools": [
            {
                "type": "function",
                "async": False,
                "messages": [
                    {
                        "type": "request-start",
                        "content": "Let me check the available viewing times for that property..."
                    },
                    {
                        "role": "assistant",
                        "type": "request-complete",
                        "content": "{{output.result}}"
                    },
                    {
                        "type": "request-failed",
                        "content": "I'm having trouble checking availability right now. Can I help you with something else?"
                    }
                ],
                "server": {
                    "url": "https://peterentalvapi-latest.onrender.com/vapi/webhook",
                    "timeoutSeconds": 20
                },
                "function": {
                    "name": "get_availability",
                    "description": "Check available viewing times for a property from the property manager's calendar. Returns available time slots for the next 7 days during business hours (9 AM - 5 PM).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "description": "Property manager user ID",
                                "type": "string",
                                "enum": ["mark@peterei.com"]
                            },
                            "property_address": {
                                "description": "Full address of the property the caller is interested in",
                                "type": "string"
                            }
                        },
                        "required": ["user_id", "property_address"]
                    }
                }
            },
            {
                "type": "function",
                "async": False,
                "messages": [
                    {
                        "type": "request-start",
                        "content": "Let me book that appointment for you..."
                    },
                    {
                        "role": "assistant",
                        "type": "request-complete",
                        "content": "{{output.result}}"
                    },
                    {
                        "type": "request-failed",
                        "content": "I couldn't complete the booking right now. Would you like me to take your information and have someone call you back?"
                    }
                ],
                "server": {
                    "url": "https://peterentalvapi-latest.onrender.com/vapi/webhook",
                    "timeoutSeconds": 20
                },
                "function": {
                    "name": "set_appointment",
                    "description": "Book a property viewing appointment in the property manager's calendar. Creates a calendar event with the viewing details and sends confirmation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "description": "Property manager user ID",
                                "type": "string",
                                "enum": ["mark@peterei.com"]
                            },
                            "start_time": {
                                "description": "Appointment start time in ISO 8601 format (e.g., 2025-10-03T14:00:00Z)",
                                "type": "string"
                            },
                            "attendee_name": {
                                "description": "Name of the person viewing the property",
                                "type": "string"
                            },
                            "attendee_email": {
                                "description": "Email address of the person viewing the property (optional)",
                                "type": "string"
                            },
                            "property_address": {
                                "description": "Full address of the property",
                                "type": "string"
                            }
                        },
                        "required": ["start_time", "user_id", "attendee_name", "property_address"]
                    }
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
    updated = response.json()
    tools = updated.get('model', {}).get('tools', [])
    print(f"\n🔧 Tools Now Attached: {len(tools)}")
    for tool in tools:
        func = tool.get('function', {})
        print(f"   ✓ {func.get('name')}")

    print("\n🎉 Assistant is fully configured!")
    print("📞 Try a voice call now at: https://peterental-nextjs.vercel.app/vapi-agent")
else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
