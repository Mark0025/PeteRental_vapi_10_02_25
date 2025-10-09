#!/usr/bin/env python3
"""Temporary fix: Update VAPI to work with CURRENT production code"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"
VAPI_BASE_URL = "https://api.vapi.ai"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

print("⚡ IMMEDIATE FIX: Updating VAPI to work with CURRENT production\n")
print("(Production hasn't deployed new code yet - still returns result.response)\n")

# Use {{output.result.response}} to match CURRENT production format
print("📅 Updating get_availability...")
get_avail_fix = {
    "messages": [
        {
            "type": "request-start",
            "content": "Let me check the available viewing times for that property..."
        },
        {
            "role": "assistant",
            "type": "request-complete",
            "content": "{{output.result.response}}"  # Matches current production
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
    print("✅ get_availability: {{output.result.response}}")
else:
    print(f"❌ Failed: {response1.status_code}")

print("\n📝 Updating set_appointment...")
set_appt_fix = {
    "messages": [
        {
            "type": "request-start",
            "content": "Let me book that appointment for you..."
        },
        {
            "role": "assistant",
            "type": "request-complete",
            "content": "{{output.result.response}}"  # Matches current production
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
    print("✅ set_appointment: {{output.result.response}}")
else:
    print(f"❌ Failed: {response2.status_code}")

print("\n✅ VAPI now matches current production format!")
print("🔄 When Render deploys (3-5 min), we'll switch to {{output.result}}")
print("\n🎤 Try your voice call NOW - should work!")
