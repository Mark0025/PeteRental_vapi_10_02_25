#!/usr/bin/env python3
"""
Test VAPI Webhook with Calendar Functions Locally
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"

def test_get_availability():
    """Test the get_availability function"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Get Availability")
    print("="*60)

    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "get_availability",
                "parameters": {
                    "user_id": "pete_admin",
                    "property_address": "123 Main Street, Apt 4B"
                }
            }
        }
    }

    print("\n📤 Request:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/vapi/webhook",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"\n📥 Response Status: {response.status_code}")
        print("\n📋 Response Body:")
        result = response.json()
        print(json.dumps(result, indent=2))

        if result.get("result"):
            print("\n✅ Function executed successfully!")
            print(f"\n💬 VAPI would say: \"{result['result'].get('response')}\"")

            # Show available slots if present
            slots = result['result'].get('available_slots', [])
            if slots:
                print(f"\n📅 Found {len(slots)} available time slots:")
                for i, slot in enumerate(slots[:5], 1):
                    print(f"   {i}. {slot.get('formatted_time')}")

        return response.status_code == 200

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_set_appointment():
    """Test the set_appointment function"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Set Appointment")
    print("="*60)

    # Schedule for tomorrow at 2 PM
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)

    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "set_appointment",
                "parameters": {
                    "user_id": "pete_admin",
                    "property_address": "123 Main Street, Apt 4B",
                    "start_time": start_time.isoformat() + "Z",
                    "attendee_name": "John Doe",
                    "attendee_email": "john.doe@example.com"
                }
            }
        }
    }

    print("\n📤 Request:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/vapi/webhook",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"\n📥 Response Status: {response.status_code}")
        print("\n📋 Response Body:")
        result = response.json()
        print(json.dumps(result, indent=2))

        if result.get("result"):
            print("\n✅ Function executed successfully!")
            print(f"\n💬 VAPI would say: \"{result['result'].get('response')}\"")

            # Show appointment details if present
            appointment = result['result'].get('appointment')
            if appointment:
                print(f"\n📝 Appointment Details:")
                print(f"   ID: {appointment.get('event_id')}")
                print(f"   Time: {appointment.get('start_time')}")
                if appointment.get('web_link'):
                    print(f"   Calendar Link: {appointment.get('web_link')}")

        return response.status_code == 200

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def check_server():
    """Check if server is running"""
    print("\n🔍 Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
    except:
        pass

    print("❌ Server is NOT running!")
    print("   Start it with: ./start_dev.sh app-only")
    return False

def check_auth():
    """Check if calendar is authorized"""
    print("\n🔍 Checking calendar authorization...")
    try:
        response = requests.get(
            f"{BASE_URL}/calendar/auth/status",
            params={"user_id": "pete_admin"},
            timeout=5
        )
        data = response.json()

        if data.get("authorized"):
            print(f"✅ Calendar is authorized!")
            print(f"   Expires: {data.get('expires_at')}")
            return True
        else:
            print("❌ Calendar is NOT authorized!")
            print("   Visit: http://localhost:8001/calendar/setup")
            return False

    except Exception as e:
        print(f"❌ Error checking auth: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 VAPI Webhook Calendar Functions Test")
    print("="*60)

    # Pre-flight checks
    if not check_server():
        return

    if not check_auth():
        return

    # Run tests
    test1_passed = test_get_availability()

    input("\n👉 Press ENTER to test appointment booking...")

    test2_passed = test_set_appointment()

    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"✅ Get Availability: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✅ Set Appointment: {'PASSED' if test2_passed else 'FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Your calendar integration is working!")
        print("\n📋 Next steps:")
        print("   1. Add tools to VAPI assistant in dashboard")
        print("   2. Test with actual voice call")
        print("   3. Deploy to production if needed")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
