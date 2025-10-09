#!/usr/bin/env python3
"""Check recent VAPI calls to see what's failing"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}"
}

print("📞 Fetching recent VAPI calls...\n")

response = requests.get(
    "https://api.vapi.ai/call?limit=5",
    headers=headers
)

if response.status_code == 200:
    calls = response.json()
    print(f"Found {len(calls)} recent calls\n")
    print("="*80)

    for i, call in enumerate(calls, 1):
        print(f"\n📞 Call #{i}")
        print(f"ID: {call.get('id')}")
        print(f"Status: {call.get('status')}")
        print(f"Created: {call.get('createdAt')}")
        print(f"Assistant: {call.get('assistantId')}")

        # Check for errors
        if 'messages' in call:
            print(f"\nMessages ({len(call['messages'])} total):")
            for msg in call['messages'][-5:]:  # Last 5 messages
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:100]  # First 100 chars
                print(f"  [{role}]: {content}")

        if 'artifact' in call:
            artifact = call['artifact']
            if 'messages' in artifact:
                print(f"\nArtifact messages:")
                for msg in artifact['messages'][-5:]:
                    print(f"  {msg}")

        print("\n" + "="*80)
else:
    print(f"Error: {response.status_code}")
    print(response.text)
