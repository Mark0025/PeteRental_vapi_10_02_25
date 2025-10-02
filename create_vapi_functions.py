#!/usr/bin/env python3
"""
Create VAPI Calendar Functions via REST API
"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"
VAPI_BASE_URL = "https://api.vapi.ai"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

# Function 1: Get Availability
get_availability_tool = {
    "type": "function",
    "messages": [
        {
            "type": "request-start",
            "content": "Let me check available viewing times..."
        }
    ],
    "function": {
        "name": "get_availability",
        "description": "Check available viewing times for a property from the property manager's calendar. Returns available time slots for the next 7 days during business hours (9 AM - 5 PM).",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Property manager user ID",
                    "default": "pete_admin"
                },
                "property_address": {
                    "type": "string",
                    "description": "Full address of the property the caller is interested in"
                }
            },
            "required": ["property_address"]
        }
    },
    "server": {
        "url": "https://peterentalvapi-latest.onrender.com/vapi/webhook",
        "timeoutSeconds": 20
    }
}

# Function 2: Set Appointment
set_appointment_tool = {
    "type": "function",
    "messages": [
        {
            "type": "request-start",
            "content": "Let me book that appointment for you..."
        }
    ],
    "function": {
        "name": "set_appointment",
        "description": "Book a property viewing appointment in the property manager's calendar. Creates a calendar event with the viewing details and sends confirmation.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Property manager user ID",
                    "default": "pete_admin"
                },
                "property_address": {
                    "type": "string",
                    "description": "Full address of the property"
                },
                "start_time": {
                    "type": "string",
                    "description": "Appointment start time in ISO 8601 format (e.g., 2025-10-02T14:00:00Z)"
                },
                "attendee_name": {
                    "type": "string",
                    "description": "Name of the person viewing the property"
                },
                "attendee_email": {
                    "type": "string",
                    "description": "Email address of the person viewing the property"
                }
            },
            "required": ["property_address", "start_time", "attendee_name"]
        }
    },
    "server": {
        "url": "https://peterentalvapi-latest.onrender.com/vapi/webhook",
        "timeoutSeconds": 20
    }
}

print("🚀 Creating VAPI Calendar Functions...\n")

# Create get_availability function
print("📅 Creating 'get_availability' function...")
response1 = requests.post(
    f"{VAPI_BASE_URL}/tool",
    headers=headers,
    json=get_availability_tool
)

if response1.status_code in [200, 201]:
    print("✅ get_availability created successfully!")
    result1 = response1.json()
    print(f"   Tool ID: {result1.get('id')}")
    print(f"   Response: {json.dumps(result1, indent=2)}\n")
else:
    print(f"❌ Failed to create get_availability")
    print(f"   Status: {response1.status_code}")
    print(f"   Response: {response1.text}\n")

# Create set_appointment function
print("📝 Creating 'set_appointment' function...")
response2 = requests.post(
    f"{VAPI_BASE_URL}/tool",
    headers=headers,
    json=set_appointment_tool
)

if response2.status_code in [200, 201]:
    print("✅ set_appointment created successfully!")
    result2 = response2.json()
    print(f"   Tool ID: {result2.get('id')}")
    print(f"   Response: {json.dumps(result2, indent=2)}\n")
else:
    print(f"❌ Failed to create set_appointment")
    print(f"   Status: {response2.status_code}")
    print(f"   Response: {response2.text}\n")

print("\n🎉 Done! Both calendar functions have been created in VAPI.")
print("\n📋 Next steps:")
print("1. Add these tools to your VAPI assistant configuration")
print("2. Test with a voice call")
print("3. Check VAPI_SETUP.md for assistant prompt configuration")
