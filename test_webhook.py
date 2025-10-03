#!/usr/bin/env python3
"""Test the VAPI webhook with get_availability"""
import requests
import json

webhook_url = "https://peterentalvapi-latest.onrender.com/vapi/webhook"

# Test payload matching VAPI's format
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

print("🔍 Testing webhook with get_availability...")
print(f"URL: {webhook_url}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

response = requests.post(webhook_url, json=payload)

print(f"Status Code: {response.status_code}")
print(f"Response:")
print(json.dumps(response.json(), indent=2))
