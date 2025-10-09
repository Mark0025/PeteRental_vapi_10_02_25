#!/usr/bin/env python3
"""Check VAPI assistant configuration"""
import requests
import json

VAPI_API_KEY = "c3a078c1-9884-4ef5-b82a-8e20f7d23a96"
ASSISTANT_ID = "24464697-8f45-4b38-b43a-d337f50c370e"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}"
}

print("🔍 Checking assistant configuration...\n")

response = requests.get(
    f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
    headers=headers
)

if response.status_code == 200:
    assistant = response.json()

    print(f"✅ Assistant: {assistant.get('name')}")
    print(f"📋 Model: {assistant.get('model', {}).get('model')}")
    print(f"\n🎯 First Message:")
    print(f"   {assistant.get('firstMessage')}\n")

    # Check if tools are attached
    server_tools = assistant.get('serverTools', [])
    print(f"🔧 Server Tools Attached: {len(server_tools)}")
    for tool in server_tools:
        tool_info = tool.get('function', {})
        print(f"   - {tool_info.get('name')}: {tool_info.get('description', 'No description')[:60]}...")

    # Check model configuration
    model_config = assistant.get('model', {})
    print(f"\n🤖 Model Config:")
    print(f"   Provider: {model_config.get('provider')}")
    print(f"   Model: {model_config.get('model')}")
    print(f"   Temperature: {model_config.get('temperature')}")

    # Check if tools are in tools array
    tools = assistant.get('tools', [])
    if tools:
        print(f"\n⚠️  Legacy 'tools' array found: {len(tools)} tools")
        for tool in tools:
            print(f"   - {tool.get('type')}: {tool.get('function', {}).get('name')}")

    # Print system prompt
    system_prompt = assistant.get('model', {}).get('messages', [{}])[0].get('content', '')
    if system_prompt:
        print(f"\n📝 System Prompt Preview:")
        print(f"   {system_prompt[:200]}...\n")

else:
    print(f"❌ Failed: {response.status_code}")
    print(response.text)
