#!/usr/bin/env python3
"""Fix VAPI tool response template to match backend format"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"
VAPI_BASE_URL = "https://api.vapi.ai"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

print("🔧 FINAL FIX: Updating VAPI response templates to {{output.result}}\n")

# Fix get_availability - use {{output.result}} to match backend's {"result": "text"}
print("📅 Fixing get_availability response template...")
get_avail_fix = {
    "messages": [
        {
            "type": "request-start",
            "content": "Let me check the available viewing times for that property..."
        },
        {
            "role": "assistant",
            "type": "request-complete",
            "content": "{{output.result}}"  # Changed from {{output.response}} to match {"result": "..."}
        },
        {
            "type": "request-failed",
            "content": "I'm having trouble checking availability right now. Can I help you with something else?"
        }
    ]
}

response1 = requests.patch(
    f"{VAPI_BASE_URL}/tool/cec6f21b-8b74-47a6-b73d-633eb9d71930",
    headers=headers,
    json=get_avail_fix
)

if response1.status_code in [200, 201]:
    print("✅ get_availability template updated to {{output.result}}!")
else:
    print(f"❌ Failed: {response1.status_code} - {response1.text}")

# Fix set_appointment
print("\n📝 Fixing set_appointment response template...")
set_appt_fix = {
    "messages": [
        {
            "type": "request-start",
            "content": "Let me book that appointment for you..."
        },
        {
            "role": "assistant",
            "type": "request-complete",
            "content": "{{output.result}}"  # Now matches {"result": "..."}
        },
        {
            "type": "request-failed",
            "content": "I couldn't complete the booking right now. Would you like me to take your information and have someone call you back?"
        }
    ]
}

response2 = requests.patch(
    f"{VAPI_BASE_URL}/tool/0903d34d-6f63-4430-b06e-a908a0056209",
    headers=headers,
    json=set_appt_fix
)

if response2.status_code in [200, 201]:
    print("✅ set_appointment template updated to {{output.result}}!")
else:
    print(f"❌ Failed: {response2.status_code} - {response2.text}")

print("\n🎉 Backend now returns: {'result': 'response text'}")
print("🎉 VAPI template now uses: {{output.result}}")
print("\n✅ Try your voice call again - it should work now!")
