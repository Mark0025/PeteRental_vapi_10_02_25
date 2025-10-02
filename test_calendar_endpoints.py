#!/usr/bin/env python3
"""
Test Calendar Integration Endpoints
====================================

Quick test script for Microsoft Calendar OAuth and VAPI integration
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your server URL
TEST_USER_ID = "test_user_123"
TEST_PROPERTY = "123 Main St, Apt 4B"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print('='*60)

def test_health_check():
    """Test basic server health"""
    print_section("Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_oauth_start():
    """Test OAuth authorization flow start"""
    print_section("Start OAuth Flow")

    try:
        response = requests.get(
            f"{BASE_URL}/calendar/auth/start",
            params={"user_id": TEST_USER_ID},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if "authorization_url" in data:
            print(f"\n🔗 Authorization URL:")
            print(f"{data['authorization_url']}")
            print(f"\n💡 Visit this URL in your browser to authorize")
            return True
        else:
            print(f"⚠️ No authorization URL in response")
            return False

    except Exception as e:
        print(f"❌ OAuth start failed: {e}")
        return False

def test_auth_status():
    """Test checking authorization status"""
    print_section("Check Authorization Status")

    try:
        response = requests.get(
            f"{BASE_URL}/calendar/auth/status",
            params={"user_id": TEST_USER_ID},
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        if data.get("authorized"):
            print("✅ User is authorized!")
        else:
            print("⚠️ User not authorized yet")

        return True

    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False

def test_vapi_get_availability():
    """Test VAPI get_availability function"""
    print_section("VAPI Function: get_availability")

    payload = {
        "functionCall": {
            "name": "get_availability",
            "parameters": {
                "user_id": TEST_USER_ID,
                "property_address": TEST_PROPERTY
            }
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/vapi/webhook",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ Get availability failed: {e}")
        return False

def test_vapi_set_appointment():
    """Test VAPI set_appointment function"""
    print_section("VAPI Function: set_appointment")

    # Create a test appointment for tomorrow at 2 PM
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_2pm = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)

    payload = {
        "functionCall": {
            "name": "set_appointment",
            "parameters": {
                "user_id": TEST_USER_ID,
                "property_address": TEST_PROPERTY,
                "start_time": tomorrow_2pm.isoformat() + "Z",
                "attendee_name": "John Doe",
                "attendee_email": "john@example.com"
            }
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/vapi/webhook",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")

        return response.status_code == 200

    except Exception as e:
        print(f"❌ Set appointment failed: {e}")
        return False

def test_environment_variables():
    """Check if required environment variables are configured"""
    print_section("Environment Configuration")

    required_vars = [
        "MICROSOFT_CLIENT_ID",
        "MICROSOFT_CLIENT_SECRET",
        "MICROSOFT_TENANT_ID"
    ]

    import os
    from dotenv import load_dotenv
    load_dotenv()

    all_configured = True
    for var in required_vars:
        value = os.getenv(var)
        if value and value != "your-client-secret-here":
            print(f"✅ {var}: configured")
        else:
            print(f"❌ {var}: missing or placeholder")
            all_configured = False

    return all_configured

def main():
    """Run all calendar endpoint tests"""
    print("🚀 Calendar Integration Endpoint Tests")
    print(f"Server: {BASE_URL}")
    print(f"Test User: {TEST_USER_ID}")

    results = {}

    # Test 1: Environment variables
    results["environment"] = test_environment_variables()

    # Test 2: Server health
    results["health"] = test_health_check()

    if not results["health"]:
        print("\n❌ Server is not running!")
        print("💡 Start the server with: ./start_dev.sh")
        return

    # Test 3: OAuth flow start
    results["oauth_start"] = test_oauth_start()

    # Test 4: Auth status
    results["auth_status"] = test_auth_status()

    # Test 5: VAPI get_availability (will fail if not authorized)
    results["get_availability"] = test_vapi_get_availability()

    # Test 6: VAPI set_appointment (will fail if not authorized)
    # Commented out by default to avoid creating test appointments
    # results["set_appointment"] = test_vapi_set_appointment()

    # Summary
    print_section("Test Summary")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")

    # Next steps
    print_section("Next Steps")

    if not results.get("environment"):
        print("1. Configure Microsoft credentials in .env file")
        print("   - MICROSOFT_CLIENT_ID")
        print("   - MICROSOFT_CLIENT_SECRET")
        print("   - MICROSOFT_TENANT_ID")

    if not results.get("health"):
        print("2. Start the development server:")
        print("   ./start_dev.sh")

    if results.get("oauth_start") and not results.get("get_availability"):
        print("3. Authorize calendar access:")
        print(f"   - Visit the authorization URL from the OAuth start test")
        print(f"   - Complete Microsoft login")
        print(f"   - Test again to verify")

    if all(results.values()):
        print("✅ All tests passed! Calendar integration is ready.")
        print("\n📋 Available endpoints:")
        print(f"  GET  {BASE_URL}/calendar/auth/start?user_id=USER_ID")
        print(f"  GET  {BASE_URL}/calendar/auth/callback?code=CODE&state=STATE")
        print(f"  GET  {BASE_URL}/calendar/auth/status?user_id=USER_ID")
        print(f"  POST {BASE_URL}/vapi/webhook (with functionCall payload)")

if __name__ == "__main__":
    main()
