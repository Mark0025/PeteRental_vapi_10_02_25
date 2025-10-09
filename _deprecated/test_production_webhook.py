#!/usr/bin/env python3
"""Test PRODUCTION webhook on Render"""
import requests
import json

# Test PRODUCTION webhook
webhook_url = "https://peterentalvapi-latest.onrender.com/vapi/webhook"

payload = {
    "message": {
        "toolCalls": [{
            "function": {
                "name": "get_availability",
                "arguments": {
                    "user_id": "mark@peterei.com",
                    "property_address": "123 Main Street"
                }
            }
        }]
    }
}

print(f"🌐 Testing PRODUCTION webhook: {webhook_url}\n")
print(f"📦 Payload:\n{json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(webhook_url, json=payload, timeout=30)

    print(f"✅ Status: {response.status_code}")
    print(f"\n📋 Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")

    print(f"\n📄 Response Body:")
    print(json.dumps(response.json(), indent=2))

    # Check if VAPI can parse this
    resp_data = response.json()
    if "response" in resp_data:
        print(f"\n✅ Has 'response' key - VAPI template should work!")
        print(f"   Value: {resp_data['response'][:100]}...")
    else:
        print(f"\n❌ Missing 'response' key - VAPI can't parse this!")

except Exception as e:
    print(f"❌ Error: {e}")
