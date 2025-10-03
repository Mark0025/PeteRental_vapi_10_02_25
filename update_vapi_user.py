#!/usr/bin/env python3
"""Update VAPI tools to use mark@peterei.com instead of pete_admin"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"
VAPI_BASE_URL = "https://api.vapi.ai"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

# Update set_appointment tool
print("📝 Updating set_appointment tool to use mark@peterei.com...")
set_appointment_update = {
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

response1 = requests.patch(
    f"{VAPI_BASE_URL}/tool/0903d34d-6f63-4430-b06e-a908a0056209",
    headers=headers,
    json=set_appointment_update
)

if response1.status_code in [200, 201]:
    print("✅ set_appointment updated successfully!")
    print(json.dumps(response1.json(), indent=2))
else:
    print(f"❌ Failed: {response1.status_code}")
    print(response1.text)

print("\n" + "="*60 + "\n")

# Update get_availability tool
print("📅 Updating get_availability tool to use mark@peterei.com...")
get_availability_update = {
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
}

response2 = requests.patch(
    f"{VAPI_BASE_URL}/tool/cec6f21b-8b74-47a6-b73d-633eb9d71930",
    headers=headers,
    json=get_availability_update
)

if response2.status_code in [200, 201]:
    print("✅ get_availability updated successfully!")
    print(json.dumps(response2.json(), indent=2))
else:
    print(f"❌ Failed: {response2.status_code}")
    print(response2.text)

print("\n🎉 Both tools updated to use mark@peterei.com!")
print("\n📋 Next: Test a voice call to set an appointment")
