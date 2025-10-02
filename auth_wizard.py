#!/usr/bin/env python3
"""
🧙 Microsoft Calendar Authorization Wizard
==========================================

Interactive wizard to connect your Microsoft Calendar
"""

import requests
import webbrowser
import json
from time import sleep
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001"
USER_ID = "pete_admin"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

def check_server():
    """Check if server is running"""
    print_info("Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print_success("Server is running!")
            return True
    except:
        pass

    print_error("Server is not running!")
    print_info("Start it with: ./start_dev.sh app-only")
    return False

def check_existing_auth():
    """Check if user is already authorized"""
    print_info("Checking existing authorization...")
    try:
        response = requests.get(
            f"{BASE_URL}/calendar/auth/status",
            params={"user_id": USER_ID},
            timeout=5
        )
        data = response.json()

        if data.get("authorized"):
            print_success(f"Already authorized! Token expires: {data.get('expires_at')}")
            return True
        else:
            print_warning("Not authorized yet")
            return False

    except Exception as e:
        print_error(f"Error checking auth status: {e}")
        return False

def start_oauth_flow():
    """Start OAuth authorization flow"""
    print_header("🔐 Step 1: OAuth Authorization")

    try:
        response = requests.get(
            f"{BASE_URL}/calendar/auth/start",
            params={"user_id": USER_ID},
            timeout=5
        )
        data = response.json()

        if "authorization_url" not in data:
            print_error(f"Failed to get authorization URL: {data}")
            return None

        auth_url = data["authorization_url"]
        print_success("Authorization URL generated!")

        return auth_url

    except Exception as e:
        print_error(f"Failed to start OAuth flow: {e}")
        return None

def open_browser_and_wait(auth_url):
    """Open browser and wait for authorization"""
    print_header("🌐 Step 2: Microsoft Login")

    print(f"{Colors.BOLD}Instructions:{Colors.ENDC}")
    print("1. Browser will open with Microsoft login")
    print("2. Log in with your Microsoft account")
    print("3. Grant calendar permissions when prompted")
    print("4. You'll be redirected to a callback URL")
    print("5. Return here after completing authorization")
    print()

    # Try to open browser
    try:
        webbrowser.open(auth_url)
        print_success("Browser opened!")
    except:
        print_warning("Couldn't open browser automatically")
        print(f"\n{Colors.BOLD}Please visit this URL:{Colors.ENDC}")
        print(f"{Colors.CYAN}{auth_url}{Colors.ENDC}\n")

    input(f"{Colors.BOLD}👉 Press ENTER after you've completed the authorization...{Colors.ENDC}")

def verify_authorization():
    """Verify that authorization was successful"""
    print_header("🔍 Step 3: Verifying Authorization")

    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                f"{BASE_URL}/calendar/auth/status",
                params={"user_id": USER_ID},
                timeout=5
            )
            data = response.json()

            if data.get("authorized"):
                print_success("Authorization verified!")
                print_info(f"Token expires: {data.get('expires_at')}")
                return True
            else:
                if attempt < max_attempts:
                    print_warning(f"Not verified yet (attempt {attempt}/{max_attempts})")
                    print_info("Waiting 2 seconds...")
                    sleep(2)

        except Exception as e:
            print_error(f"Error verifying: {e}")

    print_error("Authorization verification failed")
    return False

def test_availability():
    """Test getting calendar availability"""
    print_header("🧪 Step 4: Testing Calendar Access")

    print_info("Fetching available time slots...")

    try:
        response = requests.get(
            f"{BASE_URL}/calendar/availability",
            params={
                "user_id": USER_ID,
                "days_ahead": 7,
                "start_hour": 9,
                "end_hour": 17
            },
            timeout=15
        )
        data = response.json()

        if data.get("status") == "success":
            slots = data.get("available_slots", [])
            print_success(f"Found {len(slots)} available time slots!")

            if slots:
                print(f"\n{Colors.BOLD}📅 Next 5 available times:{Colors.ENDC}")
                for i, slot in enumerate(slots[:5], 1):
                    print(f"   {i}. {slot.get('formatted_time')}")

            return True
        else:
            print_error(f"Failed to get availability: {data.get('message')}")
            return False

    except Exception as e:
        print_error(f"Error testing availability: {e}")
        return False

def test_create_event():
    """Test creating a calendar event"""
    print_header("🗓️  Optional: Create Test Event")

    create = input(f"{Colors.BOLD}Would you like to create a test event? (y/n): {Colors.ENDC}").lower()

    if create != 'y':
        print_info("Skipping event creation")
        return True

    # Create event for tomorrow at 2 PM
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(minutes=30)

    print_info(f"Creating test event: {start_time.strftime('%A, %B %d at %I:%M %p')}")

    try:
        response = requests.post(
            f"{BASE_URL}/calendar/events",
            params={
                "user_id": USER_ID,
                "subject": "🧪 Test Event - PeteRental VAPI",
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "body": "This is a test event created by the authorization wizard."
            },
            timeout=15
        )
        data = response.json()

        if data.get("status") == "success":
            event = data.get("event", {})
            print_success("Test event created!")
            print_info(f"Event ID: {event.get('event_id')}")
            if event.get('web_link'):
                print_info(f"View in calendar: {event.get('web_link')}")
            return True
        else:
            print_error(f"Failed to create event: {data.get('message')}")
            return False

    except Exception as e:
        print_error(f"Error creating event: {e}")
        return False

def show_api_examples():
    """Show API usage examples"""
    print_header("📚 API Usage Examples")

    print(f"{Colors.BOLD}1. Get Availability:{Colors.ENDC}")
    print(f"{Colors.CYAN}curl 'http://localhost:8001/calendar/availability?user_id={USER_ID}&days_ahead=7'{Colors.ENDC}")

    print(f"\n{Colors.BOLD}2. Create Event:{Colors.ENDC}")
    print(f"{Colors.CYAN}curl -X POST 'http://localhost:8001/calendar/events?user_id={USER_ID}&subject=Meeting&start_time=2025-10-02T14:00:00Z&end_time=2025-10-02T14:30:00Z'{Colors.ENDC}")

    print(f"\n{Colors.BOLD}3. VAPI Webhook (Get Availability):{Colors.ENDC}")
    print(f"""{Colors.CYAN}curl -X POST http://localhost:8001/vapi/webhook \\
  -H "Content-Type: application/json" \\
  -d '{{
    "functionCall": {{
      "name": "get_availability",
      "parameters": {{
        "user_id": "{USER_ID}",
        "property_address": "123 Main St"
      }}
    }}
  }}'{Colors.ENDC}""")

    print(f"\n{Colors.BOLD}4. Check Authorization Status:{Colors.ENDC}")
    print(f"{Colors.CYAN}curl 'http://localhost:8001/calendar/auth/status?user_id={USER_ID}'{Colors.ENDC}")

def main():
    """Main wizard flow"""
    print_header("🧙 Microsoft Calendar Authorization Wizard")

    # Step 0: Check server
    if not check_server():
        return

    # Check if already authorized
    if check_existing_auth():
        reauth = input(f"\n{Colors.BOLD}Re-authorize anyway? (y/n): {Colors.ENDC}").lower()
        if reauth != 'y':
            print_info("Using existing authorization")
            test_availability()
            test_create_event()
            show_api_examples()
            return

    # Step 1: Start OAuth flow
    auth_url = start_oauth_flow()
    if not auth_url:
        return

    # Step 2: Open browser and wait
    open_browser_and_wait(auth_url)

    # Step 3: Verify authorization
    if not verify_authorization():
        print_error("\n❌ Authorization failed!")
        print_info("\n🔧 Troubleshooting:")
        print("   1. Check Azure app redirect URI:")
        print("      https://peterentalvapi-latest.onrender.com/calendar/auth/callback")
        print("   2. Verify permissions: Calendars.ReadWrite, User.Read")
        print("   3. Check .env file has correct credentials")
        return

    # Step 4: Test availability
    if not test_availability():
        print_warning("Availability test failed, but authorization succeeded")

    # Step 5: Optional - create test event
    test_create_event()

    # Show examples
    show_api_examples()

    # Success!
    print_header("🎉 Setup Complete!")
    print_success("Your Microsoft Calendar is connected!")
    print_info(f"User ID: {USER_ID}")
    print_info("You can now use all calendar endpoints")
    print_info("Check API_DOCS.md for full documentation")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Wizard cancelled{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Unexpected error: {e}{Colors.ENDC}")
