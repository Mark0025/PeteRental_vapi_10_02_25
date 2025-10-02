#!/usr/bin/env python3
"""
Quick Authorization Script for Microsoft Calendar
==================================================

Run this script to connect your Microsoft Calendar account
"""

import requests
import webbrowser
from time import sleep

BASE_URL = "http://localhost:8001"
USER_ID = "pete_admin"  # Your main user ID

def authorize_calendar():
    """Complete OAuth flow for calendar authorization"""

    print("🔐 Microsoft Calendar Authorization")
    print("="*60)

    # Step 1: Get authorization URL
    print("\n📋 Step 1: Getting authorization URL...")
    try:
        response = requests.get(
            f"{BASE_URL}/calendar/auth/start",
            params={"user_id": USER_ID},
            timeout=5
        )
        data = response.json()

        if "authorization_url" not in data:
            print(f"❌ Error: {data}")
            return False

        auth_url = data["authorization_url"]
        print("✅ Authorization URL generated")

    except Exception as e:
        print(f"❌ Failed to get authorization URL: {e}")
        print("💡 Make sure the server is running: ./start_dev.sh app-only")
        return False

    # Step 2: Open browser for user to authorize
    print("\n🌐 Step 2: Opening browser for Microsoft login...")
    print(f"🔗 URL: {auth_url[:80]}...")
    print("\n⚠️  IMPORTANT:")
    print("   1. Log in with your Microsoft account")
    print("   2. Grant calendar permissions")
    print("   3. You'll be redirected to the callback URL")
    print("   4. Copy the full callback URL from your browser")
    print()

    # Try to open browser automatically
    try:
        webbrowser.open(auth_url)
        print("✅ Browser opened automatically")
    except:
        print("⚠️  Couldn't open browser automatically")
        print(f"\n🔗 Please visit this URL manually:\n{auth_url}\n")

    # Step 3: Wait for user to complete authorization
    print("\n⏳ Step 3: Waiting for authorization...")
    print("   Complete the login in your browser, then come back here.")

    input("\n👉 Press ENTER after you've completed the authorization in your browser...")

    # Step 4: Check if authorization was successful
    print("\n🔍 Step 4: Checking authorization status...")

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                f"{BASE_URL}/calendar/auth/status",
                params={"user_id": USER_ID},
                timeout=5
            )
            data = response.json()

            if data.get("authorized"):
                print("✅ Authorization successful!")
                print(f"📅 Token expires: {data.get('expires_at')}")
                print(f"👤 User ID: {USER_ID}")
                return True
            else:
                if attempt < max_attempts:
                    print(f"⚠️  Not authorized yet (attempt {attempt}/{max_attempts})")
                    print("   Waiting 2 seconds...")
                    sleep(2)
                else:
                    print(f"❌ Authorization not detected after {max_attempts} attempts")
                    print("💡 The callback URL might not have been called correctly")
                    return False

        except Exception as e:
            print(f"❌ Error checking status: {e}")
            return False

    return False

def test_availability():
    """Test getting calendar availability"""
    print("\n"+"="*60)
    print("🧪 Testing Calendar Availability")
    print("="*60)

    payload = {
        "functionCall": {
            "name": "get_availability",
            "parameters": {
                "user_id": USER_ID,
                "property_address": "Test Property - 123 Main St"
            }
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/vapi/webhook",
            json=payload,
            timeout=15
        )
        data = response.json()

        print("\n📋 Response:")
        import json
        print(json.dumps(data, indent=2))

        # Check if we got availability
        result = data.get("result", {})
        if result.get("action") == "present_slots":
            slots = result.get("available_slots", [])
            print(f"\n✅ Found {len(slots)} available time slots!")
            print("\n📅 Next available times:")
            for slot in slots[:5]:
                print(f"   - {slot.get('formatted_time')}")
        elif result.get("action") == "require_auth":
            print("\n⚠️  Authorization required - please run the authorization first")
        else:
            print(f"\n⚠️  Unexpected response: {result.get('response')}")

        return True

    except Exception as e:
        print(f"❌ Failed to get availability: {e}")
        return False

def main():
    """Main authorization flow"""

    # Check if server is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print("❌ Server is not running!")
        print("💡 Start it with: ./start_dev.sh app-only")
        return

    # Run authorization
    success = authorize_calendar()

    if success:
        print("\n" + "="*60)
        print("🎉 SUCCESS! Your calendar is now connected!")
        print("="*60)

        # Ask if they want to test
        test = input("\n🧪 Would you like to test getting availability? (y/n): ").lower()

        if test == 'y':
            test_availability()

        print("\n✅ Setup complete!")
        print(f"👤 User ID: {USER_ID}")
        print("\n📚 Next steps:")
        print("   1. Test VAPI webhook endpoints")
        print("   2. Configure VAPI to use these functions")
        print("   3. Test with a voice call")

    else:
        print("\n" + "="*60)
        print("❌ Authorization Failed")
        print("="*60)
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure your Microsoft app redirect URI is set to:")
        print(f"      https://peterentalvapi-latest.onrender.com/calendar/auth/callback")
        print("   2. Check that you have the required permissions:")
        print("      - Calendars.ReadWrite")
        print("      - User.Read")
        print("   3. Verify your .env file has the correct credentials")
        print("\n💡 Try running this script again once you've checked the above")

if __name__ == "__main__":
    main()
