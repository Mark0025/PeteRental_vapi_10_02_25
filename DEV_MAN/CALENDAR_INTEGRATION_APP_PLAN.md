# APP Plan: Microsoft Calendar Integration Implementation

## 🎯 Overview
Detailed implementation plan for adding Microsoft Calendar booking to PeteRental VAPI with OAuth authentication, availability checking, and appointment creation.

## 📦 Dependencies

### New Python Packages
```toml
# Add to pyproject.toml [project.dependencies]
msal = "^1.24.0"              # Microsoft Authentication Library
msgraph-core = "^1.0.0"       # Microsoft Graph API client
python-dateutil = "^2.8.2"    # Date/time manipulation
pytz = "^2023.3"              # Timezone handling
```

### Environment Variables
```bash
# Add to .env
MICROSOFT_CLIENT_ID=your_azure_app_client_id
MICROSOFT_CLIENT_SECRET=your_azure_app_client_secret
MICROSOFT_TENANT_ID=common  # or specific tenant
MICROSOFT_REDIRECT_URI=https://peterentalvapi-latest.onrender.com/calendar/auth/callback
```

### Azure AD App Registration
1. Go to Azure Portal → Azure Active Directory → App Registrations
2. Create new registration:
   - Name: PeteRental Calendar Integration
   - Supported account types: Accounts in any organizational directory
   - Redirect URI: Web → `https://peterentalvapi-latest.onrender.com/calendar/auth/callback`
3. Required API Permissions:
   - `Calendars.ReadWrite` (Delegated)
   - `User.Read` (Delegated)
4. Generate client secret in Certificates & secrets

## 🗂️ File Structure

```
peterental_vapi/
├── src/
│   ├── calendar/
│   │   ├── __init__.py
│   │   ├── microsoft_oauth.py      # OAuth flow handler
│   │   ├── microsoft_calendar.py   # Graph API wrapper
│   │   ├── models.py                # Pydantic models
│   │   └── token_manager.py        # Token storage & refresh
│   ├── vapi/
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   └── calendar_functions.py  # VAPI function handlers
│   │   └── api/
│   │       └── vapi_router.py       # Updated with calendar functions
├── data/
│   ├── calendar_tokens.json         # Token database
│   └── rentals.json                 # Existing rental database
├── tests/
│   ├── test_oauth.py
│   ├── test_calendar.py
│   └── test_vapi_functions.py
└── main.py                          # Updated with calendar routes
```

## 📝 Implementation Details

### 1. Token Database Schema (data/calendar_tokens.json)

```json
{
  "tokens": {
    "+15555551234": {
      "user_id": "+15555551234",
      "access_token": "eyJ0eXAiOiJKV1Q...",
      "refresh_token": "0.AXoA...",
      "expires_at": "2025-09-30T14:30:00Z",
      "calendar_email": "manager@property.com",
      "created_at": "2025-09-30T13:00:00Z",
      "updated_at": "2025-09-30T13:30:00Z",
      "token_type": "Bearer",
      "scope": "Calendars.ReadWrite User.Read"
    }
  },
  "metadata": {
    "last_updated": "2025-09-30T13:30:00Z",
    "version": "1.0",
    "total_users": 1
  }
}
```

### 2. Microsoft OAuth Handler (src/calendar/microsoft_oauth.py)

```python
from msal import ConfidentialClientApplication
from typing import Dict, Optional
import os
from datetime import datetime, timedelta

class MicrosoftOAuth:
    """Handle Microsoft OAuth 2.0 flow for calendar access"""

    def __init__(self):
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID", "common")
        self.redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")

        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["Calendars.ReadWrite", "User.Read"]

        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )

    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=state
        )
        return auth_url

    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        result = self.app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )

        if "error" in result:
            raise Exception(f"Token exchange failed: {result.get('error_description')}")

        return {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token"),
            "expires_at": datetime.now() + timedelta(seconds=result["expires_in"]),
            "token_type": result["token_type"],
            "scope": " ".join(result.get("scope", []))
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh expired access token"""
        result = self.app.acquire_token_by_refresh_token(
            refresh_token=refresh_token,
            scopes=self.scopes
        )

        if "error" in result:
            raise Exception(f"Token refresh failed: {result.get('error_description')}")

        return {
            "access_token": result["access_token"],
            "expires_at": datetime.now() + timedelta(seconds=result["expires_in"])
        }
```

### 3. Token Manager (src/calendar/token_manager.py)

```python
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from loguru import logger

class TokenManager:
    """Manage calendar tokens with JSON storage"""

    def __init__(self, db_path: str = "data/calendar_tokens.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize token database if not exists"""
        if not self.db_path.exists():
            self._write_database({
                "tokens": {},
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_users": 0
                }
            })

    def _read_database(self) -> Dict:
        """Read token database"""
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def _write_database(self, data: Dict):
        """Write token database"""
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def store_token(self, user_id: str, token_data: Dict):
        """Store or update user token"""
        db = self._read_database()

        db["tokens"][user_id] = {
            "user_id": user_id,
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": token_data["expires_at"].isoformat() if isinstance(token_data["expires_at"], datetime) else token_data["expires_at"],
            "updated_at": datetime.now().isoformat(),
            "created_at": db["tokens"].get(user_id, {}).get("created_at", datetime.now().isoformat()),
            **{k: v for k, v in token_data.items() if k not in ["access_token", "refresh_token", "expires_at"]}
        }

        db["metadata"]["total_users"] = len(db["tokens"])
        self._write_database(db)
        logger.info(f"💾 Stored token for user: {user_id}")

    def get_token(self, user_id: str) -> Optional[Dict]:
        """Get user token if exists and valid"""
        db = self._read_database()
        token_data = db["tokens"].get(user_id)

        if not token_data:
            return None

        # Check if token expired
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if datetime.now() >= expires_at:
            logger.warning(f"⚠️ Token expired for user: {user_id}")
            token_data["is_expired"] = True

        return token_data

    def delete_token(self, user_id: str):
        """Delete user token"""
        db = self._read_database()
        if user_id in db["tokens"]:
            del db["tokens"][user_id]
            db["metadata"]["total_users"] = len(db["tokens"])
            self._write_database(db)
            logger.info(f"🗑️ Deleted token for user: {user_id}")
```

### 4. Microsoft Calendar Manager (src/calendar/microsoft_calendar.py)

```python
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import pytz

class MicrosoftCalendar:
    """Microsoft Graph API calendar operations"""

    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def get_availability(
        self,
        days_ahead: int = 7,
        start_hour: int = 9,
        end_hour: int = 17,
        slot_duration: int = 30
    ) -> List[Dict]:
        """Get available time slots for next N days"""

        # Query calendar for free/busy times
        start_time = datetime.now().replace(hour=0, minute=0, second=0)
        end_time = start_time + timedelta(days=days_ahead)

        schedule_url = f"{self.GRAPH_API_ENDPOINT}/me/calendar/getSchedule"

        payload = {
            "schedules": ["me"],
            "startTime": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "endTime": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            },
            "availabilityViewInterval": slot_duration
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(schedule_url, headers=self.headers, json=payload)
            response.raise_for_status()
            schedule_data = response.json()

        # Parse availability and find free slots
        available_slots = []
        for day in range(days_ahead):
            current_day = start_time + timedelta(days=day)

            # Skip weekends
            if current_day.weekday() >= 5:
                continue

            # Generate time slots for business hours
            for hour in range(start_hour, end_hour):
                for minute in [0, 30] if slot_duration == 30 else [0]:
                    slot_start = current_day.replace(hour=hour, minute=minute)
                    slot_end = slot_start + timedelta(minutes=slot_duration)

                    # Check if slot is free (simplified - would parse schedule_data properly)
                    available_slots.append({
                        "start_time": slot_start.isoformat(),
                        "end_time": slot_end.isoformat(),
                        "duration_minutes": slot_duration,
                        "formatted_time": slot_start.strftime("%A, %B %d at %I:%M %p")
                    })

        logger.info(f"📅 Found {len(available_slots)} available slots")
        return available_slots[:10]  # Return top 10 slots

    async def create_appointment(
        self,
        start_time: datetime,
        end_time: datetime,
        subject: str,
        body: str,
        attendee_email: Optional[str] = None
    ) -> Dict:
        """Create calendar appointment"""

        event_url = f"{self.GRAPH_API_ENDPOINT}/me/calendar/events"

        event_data = {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body
            },
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            },
            "isOnlineMeeting": False,
            "reminderMinutesBeforeStart": 60
        }

        if attendee_email:
            event_data["attendees"] = [{
                "emailAddress": {
                    "address": attendee_email
                },
                "type": "required"
            }]

        async with httpx.AsyncClient() as client:
            response = await client.post(event_url, headers=self.headers, json=event_data)
            response.raise_for_status()
            event_result = response.json()

        logger.info(f"✅ Created appointment: {event_result['id']}")

        return {
            "event_id": event_result["id"],
            "subject": event_result["subject"],
            "start_time": event_result["start"]["dateTime"],
            "end_time": event_result["end"]["dateTime"],
            "web_link": event_result.get("webLink")
        }

    async def check_conflict(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if time slot has a conflict"""
        schedule_url = f"{self.GRAPH_API_ENDPOINT}/me/calendar/getSchedule"

        payload = {
            "schedules": ["me"],
            "startTime": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "endTime": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(schedule_url, headers=self.headers, json=payload)
            response.raise_for_status()
            schedule_data = response.json()

        # Check if any schedule items exist for this time
        schedules = schedule_data.get("value", [])
        if schedules and len(schedules) > 0:
            schedule_items = schedules[0].get("scheduleItems", [])
            return len(schedule_items) > 0

        return False
```

### 5. VAPI Calendar Functions (src/vapi/functions/calendar_functions.py)

```python
from fastapi import HTTPException
from typing import Dict, Any
from datetime import datetime
from loguru import logger
from calendar.microsoft_oauth import MicrosoftOAuth
from calendar.microsoft_calendar import MicrosoftCalendar
from calendar.token_manager import TokenManager

class CalendarFunctions:
    """VAPI custom function handlers for calendar operations"""

    def __init__(self):
        self.oauth = MicrosoftOAuth()
        self.token_manager = TokenManager()

    async def handle_get_availability(self, parameters: Dict[str, Any]) -> Dict:
        """
        VAPI Function: get_availability

        Parameters:
        - property_address: string (rental property address)
        - user_id: string (caller phone number)
        """
        try:
            user_id = parameters.get("user_id")
            property_address = parameters.get("property_address", "")

            if not user_id:
                return {
                    "result": {
                        "response": "I need to connect your calendar first. Please authorize calendar access.",
                        "action": "require_auth"
                    }
                }

            # Get user token
            token_data = self.token_manager.get_token(user_id)

            if not token_data:
                return {
                    "result": {
                        "response": "You haven't connected your calendar yet. Would you like me to send you an authorization link?",
                        "action": "require_auth"
                    }
                }

            # Check if token expired and refresh
            if token_data.get("is_expired"):
                try:
                    new_token = await self.oauth.refresh_access_token(token_data["refresh_token"])
                    self.token_manager.store_token(user_id, new_token)
                    token_data = self.token_manager.get_token(user_id)
                except Exception as e:
                    logger.error(f"Token refresh failed: {e}")
                    return {
                        "result": {
                            "response": "Your calendar authorization expired. Please re-authorize calendar access.",
                            "action": "require_auth"
                        }
                    }

            # Get availability
            calendar = MicrosoftCalendar(token_data["access_token"])
            available_slots = await calendar.get_availability()

            if not available_slots:
                return {
                    "result": {
                        "response": f"Unfortunately, there are no available viewing times in the next week for {property_address}. Would you like to leave your contact information?",
                        "action": "no_availability"
                    }
                }

            # Format response for voice
            response = f"I have several viewing times available for {property_address}. "
            response += "Here are the next available slots: "

            for i, slot in enumerate(available_slots[:3], 1):
                response += f"{slot['formatted_time']}, "

            response += "Which time works best for you?"

            return {
                "result": {
                    "response": response,
                    "available_slots": available_slots,
                    "action": "present_slots"
                }
            }

        except Exception as e:
            logger.error(f"❌ get_availability error: {e}")
            return {
                "result": {
                    "response": "I'm having trouble checking availability right now. Can I help you with something else?",
                    "action": "error"
                }
            }

    async def handle_set_appointment(self, parameters: Dict[str, Any]) -> Dict:
        """
        VAPI Function: set_appointment

        Parameters:
        - property_address: string
        - start_time: ISO datetime string
        - user_id: string (caller phone number)
        - attendee_name: string (optional)
        - attendee_email: string (optional)
        """
        try:
            user_id = parameters.get("user_id")
            property_address = parameters.get("property_address")
            start_time_str = parameters.get("start_time")
            attendee_name = parameters.get("attendee_name", "")
            attendee_email = parameters.get("attendee_email")

            # Parse start time
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = start_time + timedelta(minutes=30)

            # Get token
            token_data = self.token_manager.get_token(user_id)

            if not token_data or token_data.get("is_expired"):
                return {
                    "result": {
                        "response": "I need to connect your calendar first to book appointments.",
                        "action": "require_auth"
                    }
                }

            # Check for conflicts
            calendar = MicrosoftCalendar(token_data["access_token"])
            has_conflict = await calendar.check_conflict(start_time, end_time)

            if has_conflict:
                return {
                    "result": {
                        "response": f"I'm sorry, but {start_time.strftime('%I:%M %p on %A, %B %d')} is no longer available. Would you like to check other available times?",
                        "action": "conflict"
                    }
                }

            # Create appointment
            subject = f"Property Viewing - {property_address}"
            body = f"""
            <html>
            <body>
                <h2>Property Viewing Appointment</h2>
                <p><strong>Property:</strong> {property_address}</p>
                <p><strong>Attendee:</strong> {attendee_name or 'Guest'}</p>
                <p><strong>Contact:</strong> {user_id}</p>
                <p>Please arrive 5 minutes early.</p>
            </body>
            </html>
            """

            appointment = await calendar.create_appointment(
                start_time=start_time,
                end_time=end_time,
                subject=subject,
                body=body,
                attendee_email=attendee_email
            )

            # Success response
            formatted_time = start_time.strftime("%I:%M %p on %A, %B %d")
            response = f"Perfect! I've booked your viewing for {formatted_time} at {property_address}. "
            response += "You'll receive a calendar invitation shortly. Is there anything else I can help you with?"

            return {
                "result": {
                    "response": response,
                    "appointment": appointment,
                    "action": "booked"
                }
            }

        except Exception as e:
            logger.error(f"❌ set_appointment error: {e}")
            return {
                "result": {
                    "response": "I couldn't complete the booking right now. Would you like me to take your information and have someone call you back?",
                    "action": "error"
                }
            }
```

### 6. FastAPI Route Integration (main.py updates)

```python
# Add to main.py

from src.calendar.microsoft_oauth import MicrosoftOAuth
from src.vapi.functions.calendar_functions import CalendarFunctions
import secrets

# Initialize calendar services
oauth_handler = MicrosoftOAuth()
calendar_functions = CalendarFunctions()

@app.get("/calendar/auth/start")
async def start_calendar_auth(user_id: str):
    """Initiate OAuth flow for calendar access"""
    state = secrets.token_urlsafe(32)
    # Store state with user_id for validation (would use Redis/database)
    auth_url = oauth_handler.get_authorization_url(state)
    return {
        "authorization_url": auth_url,
        "message": "Visit this URL to authorize calendar access"
    }

@app.get("/calendar/auth/callback")
async def calendar_auth_callback(code: str, state: str):
    """Handle OAuth callback"""
    try:
        # Validate state (simplified - would check against stored state)
        token_data = await oauth_handler.exchange_code_for_token(code)

        # Store token (user_id would come from state)
        user_id = "temp_user"  # Would extract from state
        calendar_functions.token_manager.store_token(user_id, token_data)

        return {
            "status": "success",
            "message": "Calendar connected successfully!"
        }
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/calendar/auth/status")
async def calendar_auth_status(user_id: str):
    """Check if user has authorized calendar access"""
    token_data = calendar_functions.token_manager.get_token(user_id)
    return {
        "authorized": token_data is not None,
        "expires_at": token_data.get("expires_at") if token_data else None
    }

# Update VAPI webhook to handle calendar functions
@app.post("/vapi/webhook")
async def vapi_webhook_updated(request: dict):
    """Enhanced webhook with calendar function support"""

    function_call = request.get('functionCall', {})
    function_name = function_call.get('name')

    if function_name == 'get_availability':
        return await calendar_functions.handle_get_availability(
            function_call.get('parameters', {})
        )

    elif function_name == 'set_appointment':
        return await calendar_functions.handle_set_appointment(
            function_call.get('parameters', {})
        )

    # ... existing webhook logic for rental search
```

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_oauth.py
async def test_authorization_url():
    oauth = MicrosoftOAuth()
    url = oauth.get_authorization_url("test_state")
    assert "login.microsoftonline.com" in url
    assert "Calendars.ReadWrite" in url

# tests/test_calendar.py
@pytest.mark.asyncio
async def test_get_availability():
    # Mock Graph API response
    calendar = MicrosoftCalendar("mock_token")
    slots = await calendar.get_availability(days_ahead=7)
    assert len(slots) > 0
    assert "start_time" in slots[0]
```

### Integration Tests
```bash
# Test OAuth flow
curl http://localhost:8000/calendar/auth/start?user_id=+15555551234

# Test availability check
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "functionCall": {
      "name": "get_availability",
      "parameters": {
        "property_address": "123 Main St",
        "user_id": "+15555551234"
      }
    }
  }'
```

## 📊 Success Criteria

1. ✅ OAuth flow completes without errors
2. ✅ Tokens stored and retrieved correctly
3. ✅ Token refresh works automatically
4. ✅ get_availability returns valid time slots
5. ✅ set_appointment creates calendar events
6. ✅ VAPI functions return proper responses
7. ✅ API documentation updated
8. ✅ All tests passing

## 🚀 Deployment Checklist

- [ ] Environment variables set in Render
- [ ] Azure AD app configured with redirect URI
- [ ] Dependencies installed (msal, msgraph-core)
- [ ] Database directory created for tokens
- [ ] FastAPI docs updated with calendar endpoints
- [ ] Smoke tests run on production
