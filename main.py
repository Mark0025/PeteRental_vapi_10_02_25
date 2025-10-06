#!/usr/bin/env python3
"""
Pete Rental VAPI Server
======================

Simple FastAPI server with DuckDuckGo website search for VAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from pathlib import Path
import os
import sys

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Import rental database
from rental_database import rental_db

# Import Playwright scraper
from playwright_scraper import scrape_rentals_sync

# Import calendar functions
from src.calendar.microsoft_oauth import MicrosoftOAuth
from src.calendar.token_manager import TokenManager
from src.vapi.functions.calendar_functions import calendar_functions
import secrets
import httpx

app = FastAPI(
    title="Pete Rental VAPI Server",
    description="Voice AI with DuckDuckGo Website Search + Calendar Booking",
    version="1.0.0"
)

# CORS middleware - allow frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://peterental-nextjs.vercel.app",  # Production
        "https://peterental-nextjs-octs8yxcr-mark-carpenters-projects.vercel.app",  # Preview
        "https://*.vercel.app",  # Allow all Vercel preview deployments
        "https://peterentalvapi-latest.onrender.com",  # Render production
        "https://vapi.ai",  # VAPI dashboard
        "https://*.vapi.ai",  # VAPI webhook servers
        "http://localhost:3000",  # Local development
        "http://localhost:3001",
        "http://localhost:8000",
        "http://localhost:8001",
        "*",  # Allow all origins (VAPI webhooks come from various IPs)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize calendar services
oauth_handler = MicrosoftOAuth()
token_manager = TokenManager()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Pete Rental VAPI Server",
        "version": "1.0.0",
        "status": "running",
        "features": ["DuckDuckGo Search", "VAPI Webhooks", "Microsoft Calendar"],
        "links": {
            "api_docs": "/docs",
            "calendar_setup": "/calendar/setup",
            "health": "/health"
        }
    }

@app.get("/calendar/setup", response_class=HTMLResponse)
async def calendar_setup_page():
    """Web UI for calendar authorization"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PeteRental Calendar Setup</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
            }
            .input-group {
                margin: 20px 0;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 600;
            }
            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                box-sizing: border-box;
                transition: border-color 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                margin-top: 20px;
                transition: transform 0.2s;
            }
            button:hover {
                transform: translateY(-2px);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .status {
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                display: none;
            }
            .status.success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .status.error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .status.info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            .info-box {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #667eea;
            }
            .info-box h3 {
                margin-top: 0;
                color: #667eea;
            }
            .info-box ul {
                margin: 10px 0;
                padding-left: 20px;
            }
            .loader {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-left: 10px;
                vertical-align: middle;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗓️ Microsoft Calendar Setup</h1>
            <p class="subtitle">Connect your Microsoft Calendar to enable appointment booking</p>

            <div class="info-box">
                <h3>ℹ️ What is User ID?</h3>
                <p><strong>User ID</strong> is just a unique identifier for you. It can be:</p>
                <ul>
                    <li>Your email: <code>pete@example.com</code></li>
                    <li>A simple name: <code>pete_admin</code></li>
                    <li>Any unique string you choose</li>
                </ul>
                <p>💡 Use the same User ID each time to access your calendar connection.</p>
            </div>

            <div class="input-group">
                <label for="userId">Your User ID:</label>
                <input type="text" id="userId" placeholder="e.g., pete_admin" value="pete_admin">
            </div>

            <div id="status" class="status"></div>

            <button id="checkBtn" onclick="checkStatus()">Check Authorization Status</button>
            <button id="authBtn" onclick="startAuth()">🔐 Connect Microsoft Calendar</button>

            <div class="info-box" style="margin-top: 30px;">
                <h3>📚 API Endpoints</h3>
                <ul>
                    <li><strong>API Documentation:</strong> <a href="/docs" target="_blank">/docs</a></li>
                    <li><strong>Get Availability:</strong> GET /calendar/availability?user_id=YOUR_ID</li>
                    <li><strong>Create Event:</strong> POST /calendar/events</li>
                </ul>
            </div>
        </div>

        <script>
            async function checkStatus() {
                const userId = document.getElementById('userId').value;
                const statusDiv = document.getElementById('status');
                const checkBtn = document.getElementById('checkBtn');

                if (!userId) {
                    showStatus('error', 'Please enter a User ID');
                    return;
                }

                checkBtn.innerHTML = 'Checking... <div class="loader"></div>';
                checkBtn.disabled = true;

                try {
                    const response = await fetch(`/calendar/auth/status?user_id=${encodeURIComponent(userId)}`);
                    const data = await response.json();

                    if (data.authorized) {
                        showStatus('success', `✅ Authorized! Token expires: ${data.expires_at || 'Unknown'}`);
                    } else {
                        showStatus('info', '⚠️ Not authorized yet. Click "Connect Microsoft Calendar" to get started.');
                    }
                } catch (error) {
                    showStatus('error', `❌ Error: ${error.message}`);
                } finally {
                    checkBtn.innerHTML = 'Check Authorization Status';
                    checkBtn.disabled = false;
                }
            }

            function startAuth() {
                const userId = document.getElementById('userId').value;

                if (!userId) {
                    showStatus('error', 'Please enter a User ID');
                    return;
                }

                // Direct navigation to auth endpoint (no fetch, avoid CORS redirect issues)
                showStatus('success', '🔗 Redirecting to Microsoft login...');
                window.location.href = `/calendar/auth/start?user_id=${encodeURIComponent(userId)}`;
            }

            function showStatus(type, message) {
                const statusDiv = document.getElementById('status');
                statusDiv.className = `status ${type}`;
                statusDiv.textContent = message;
                statusDiv.style.display = 'block';
            }

            // Check status on load
            window.onload = () => {
                checkStatus();
            };
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "peterental-vapi"
    }

@app.get("/debug/last-vapi-request")
async def get_last_vapi_request():
    """Debug endpoint to see what VAPI last sent"""
    import json
    import os
    try:
        if os.path.exists("/tmp/last_vapi_request.json"):
            with open("/tmp/last_vapi_request.json", "r") as f:
                return json.load(f)
        else:
            return {"error": "No request captured yet. Make a VAPI call first."}
    except Exception as e:
        return {"error": str(e)}

# Calendar OAuth Endpoints
@app.get("/calendar/auth/start")
async def start_calendar_auth(user_id: str):
    """Initiate OAuth flow for calendar access - redirects to Microsoft"""
    try:
        state = f"{user_id}:{secrets.token_urlsafe(16)}"
        auth_url = oauth_handler.get_authorization_url(state)
        # Redirect directly to Microsoft OAuth page
        return RedirectResponse(url=auth_url)
    except Exception as e:
        return {"error": str(e), "configured": False}

@app.get("/calendar/auth/callback")
async def calendar_auth_callback(code: str, state: str):
    """Handle OAuth callback - redirects to frontend"""
    try:
        # Extract user_id from state
        user_id = state.split(":")[0] if ":" in state else "default_user"

        token_data = await oauth_handler.exchange_code_for_token(code)
        token_manager.store_token(user_id, token_data)

        # Redirect to frontend Users page with success
        frontend_url = os.getenv("FRONTEND_URL", "https://peterental-nextjs.vercel.app")
        return RedirectResponse(url=f"{frontend_url}/users?auth=success&email={user_id}")
    except Exception as e:
        from loguru import logger
        logger.error(f"OAuth callback error: {e}")
        # Redirect to frontend with error
        frontend_url = os.getenv("FRONTEND_URL", "https://peterental-nextjs.vercel.app")
        return RedirectResponse(url=f"{frontend_url}/users?auth=error&message={str(e)}")

@app.get("/calendar/auth/status")
async def calendar_auth_status(user_id: str):
    """Check if user has authorized calendar access"""
    token_data = token_manager.get_token(user_id)
    return {
        "authorized": token_data is not None and not token_data.get("is_expired", False),
        "expires_at": token_data.get("expires_at") if token_data else None
    }

# Direct Calendar Event Endpoints (for testing)
@app.post("/calendar/events")
async def create_calendar_event(
    user_id: str,
    subject: str,
    start_time: str,
    end_time: str,
    body: str = "",
    attendee_email: str = None
):
    """
    Direct endpoint to create calendar event

    Example:
    POST /calendar/events?user_id=pete_admin&subject=Test Event&start_time=2025-10-02T14:00:00Z&end_time=2025-10-02T14:30:00Z
    """
    from src.calendar.microsoft_calendar import MicrosoftCalendar
    from datetime import datetime as dt
    from loguru import logger

    try:
        # Get valid token
        token_data = token_manager.get_token(user_id)
        if not token_data or token_data.get("is_expired"):
            return {
                "status": "error",
                "message": "Not authorized. Please authorize calendar access first.",
                "auth_url": f"/calendar/auth/start?user_id={user_id}"
            }

        # Parse times
        start_dt = dt.fromisoformat(start_time.replace('Z', '+00:00'))
        end_dt = dt.fromisoformat(end_time.replace('Z', '+00:00'))

        # Create event
        calendar = MicrosoftCalendar(token_data["access_token"])
        event = await calendar.create_appointment(
            start_time=start_dt,
            end_time=end_dt,
            subject=subject,
            body=body,
            attendee_email=attendee_email
        )

        logger.info(f"✅ Created event via direct endpoint: {event['event_id']}")

        return {
            "status": "success",
            "event": event
        }

    except Exception as e:
        logger.error(f"❌ Create event error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/calendar/availability")
async def get_calendar_availability(
    user_id: str,
    days_ahead: int = 7,
    start_hour: int = 9,
    end_hour: int = 17
):
    """
    Direct endpoint to get calendar availability

    Example:
    GET /calendar/availability?user_id=pete_admin&days_ahead=7
    """
    from src.calendar.microsoft_calendar import MicrosoftCalendar
    from loguru import logger

    try:
        # Get valid token
        token_data = token_manager.get_token(user_id)
        if not token_data or token_data.get("is_expired"):
            return {
                "status": "error",
                "message": "Not authorized. Please authorize calendar access first.",
                "auth_url": f"/calendar/auth/start?user_id={user_id}"
            }

        # Get availability
        calendar = MicrosoftCalendar(token_data["access_token"])
        slots = await calendar.get_availability(
            days_ahead=days_ahead,
            start_hour=start_hour,
            end_hour=end_hour
        )

        logger.info(f"✅ Retrieved {len(slots)} available slots via direct endpoint")

        return {
            "status": "success",
            "user_id": user_id,
            "available_slots": slots,
            "total_slots": len(slots)
        }

    except Exception as e:
        logger.error(f"❌ Get availability error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/calendar/events")
async def get_calendar_events(
    user_id: str,
    days_ahead: int = 14
):
    """
    Get upcoming calendar events for a user

    Example:
    GET /calendar/events?user_id=mark@peterei.com&days_ahead=14
    """
    from src.calendar.microsoft_calendar import MicrosoftCalendar
    from datetime import datetime, timedelta
    from loguru import logger

    try:
        # Get valid token
        token_data = token_manager.get_token(user_id)
        if not token_data or token_data.get("is_expired"):
            return {
                "status": "error",
                "message": "Not authorized. Please authorize calendar access first.",
                "auth_url": f"/calendar/auth/start?user_id={user_id}"
            }

        # Fetch events using Graph API
        calendar = MicrosoftCalendar(token_data["access_token"])

        # Calculate time range
        start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=days_ahead)

        # Use calendarView endpoint
        import httpx
        events_url = f"{calendar.GRAPH_API_ENDPOINT}/me/calendarView"
        params = {
            "startDateTime": start_time.isoformat() + "Z",
            "endDateTime": end_time.isoformat() + "Z",
            "$orderby": "start/dateTime",
            "$top": 50
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(events_url, headers=calendar.headers, params=params)
            response.raise_for_status()
            events_data = response.json()

        # Format events for frontend
        events = []
        for event in events_data.get("value", []):
            events.append({
                "id": event["id"],
                "subject": event.get("subject", "No Subject"),
                "start_time": event["start"]["dateTime"],
                "end_time": event["end"]["dateTime"],
                "location": event.get("location", {}).get("displayName", ""),
                "attendees": [
                    {
                        "name": attendee.get("emailAddress", {}).get("name", ""),
                        "email": attendee.get("emailAddress", {}).get("address", "")
                    }
                    for attendee in event.get("attendees", [])
                ],
                "is_online_meeting": event.get("isOnlineMeeting", False),
                "web_link": event.get("webLink")
            })

        logger.info(f"✅ Retrieved {len(events)} calendar events for {user_id}")

        return {
            "status": "success",
            "user_id": user_id,
            "events": events,
            "total_events": len(events)
        }

    except Exception as e:
        logger.error(f"❌ Get events error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/database/status")
async def database_status():
    """Get rental database status and statistics"""
    try:
        stats = rental_db.get_database_stats()
        return {
            "status": "success",
            "database_stats": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/database/rentals/{website}")
async def get_rentals_for_website(website: str):
    """Get all rentals for a specific website"""
    try:
        rentals = rental_db.get_rentals_for_website(website)
        return {
            "status": "success",
            "website": website,
            "rental_count": len(rentals),
            "rentals": rentals
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/database/available")
async def get_available_rentals():
    """Get all available rentals with availability dates"""
    try:
        from datetime import datetime
        
        all_rentals = rental_db.get_all_rentals()
        available_rentals = []
        
        for rental in all_rentals:
            rental_data = rental["data"]
            if "available_date" in rental_data:
                # Parse the availability date
                avail_date = rental_data["available_date"]
                
                # Check if it's immediate
                if avail_date.lower() in ["immediate", "now"]:
                    rental_data["availability_status"] = "Available Now"
                    rental_data["days_until_available"] = 0
                else:
                    try:
                        # Try to parse date like "July 15" or "August 4"
                        current_year = datetime.now().year
                        date_str = f"{avail_date} {current_year}"
                        
                        # Handle different date formats
                        for fmt in ["%B %d %Y", "%b %d %Y"]:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            # If we can't parse, just use the original string
                            parsed_date = None
                        
                        if parsed_date:
                            days_until = (parsed_date - datetime.now()).days
                            if days_until < 0:
                                # Date has passed, assume available now
                                rental_data["availability_status"] = "Available Now"
                                rental_data["days_until_available"] = 0
                            else:
                                rental_data["availability_status"] = f"Available {avail_date}"
                                rental_data["days_until_available"] = days_until
                        else:
                            rental_data["availability_status"] = f"Available {avail_date}"
                            rental_data["days_until_available"] = "Unknown"
                    except Exception as date_error:
                        rental_data["availability_status"] = f"Available {avail_date}"
                        rental_data["days_until_available"] = "Unknown"
                
                available_rentals.append(rental_data)
        
        # Sort by availability (immediate first, then by date)
        available_rentals.sort(key=lambda x: x.get("days_until_available", 999))
        
        return {
            "status": "success",
            "total_available": len(available_rentals),
            "current_date": datetime.now().strftime("%B %d, %Y"),
            "rentals": available_rentals
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
    }

# Simple VAPI webhook endpoint
@app.get("/vapi/assistants")
async def get_vapi_assistants():
    """
    Fetch all VAPI assistants from the VAPI API
    Returns list of assistants with their configurations
    """
    from loguru import logger

    try:
        vapi_api_key = os.getenv("VAPI_API_KEY", "c3a078c1-9884-4ef5-b82a-8e20f7d23a96")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.vapi.ai/assistant",
                headers={"Authorization": f"Bearer {vapi_api_key}"}
            )

            if response.status_code == 200:
                assistants = response.json()
                logger.info(f"✅ Fetched {len(assistants)} assistants from VAPI")

                # Format for frontend consumption
                formatted_assistants = []
                for assistant in assistants:
                    formatted_assistants.append({
                        "id": assistant.get("id"),
                        "name": assistant.get("name"),
                        "model": assistant.get("model", {}).get("model"),
                        "voice": assistant.get("voice", {}).get("voiceId"),
                        "firstMessage": assistant.get("firstMessage"),
                        "tools": assistant.get("model", {}).get("tools", []),
                        "createdAt": assistant.get("createdAt"),
                        "updatedAt": assistant.get("updatedAt")
                    })

                return {
                    "status": "success",
                    "assistants": formatted_assistants,
                    "count": len(formatted_assistants)
                }
            else:
                logger.error(f"❌ Failed to fetch assistants: {response.status_code}")
                return {
                    "status": "error",
                    "message": f"VAPI API returned {response.status_code}",
                    "assistants": []
                }
    except Exception as e:
        logger.error(f"❌ Error fetching assistants: {e}")
        return {
            "status": "error",
            "message": str(e),
            "assistants": []
        }

@app.post("/vapi/webhook")
async def vapi_webhook(request: dict):
    """
    Simple VAPI webhook handler with DuckDuckGo search
    """
    try:
        from loguru import logger
        import json
        from datetime import datetime

        # VERBOSE LOGGING: Log the full request to see what VAPI actually sends
        timestamp = datetime.now().isoformat()
        logger.info("="*80)
        logger.info(f"🔍 VAPI WEBHOOK REQUEST RECEIVED at {timestamp}")
        logger.info("="*80)
        logger.info(f"📦 Full Request JSON:\n{json.dumps(request, indent=2)}")
        logger.info("="*80)

        # Also save to a file we can retrieve via HTTP
        try:
            with open("/tmp/last_vapi_request.json", "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "request": request
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save request to file: {e}")
        
        # Extract website directly from request body (VAPI sends it directly)
        website = request.get('website', '')
        
        # Fallback: check if it's nested in body or other locations
        if not website:
            website = request.get('body', {}).get('website', '')
        if not website:
            website = request.get('parameters', {}).get('website', '')
        if not website:
            website = request.get('functionCall', {}).get('parameters', {}).get('website', '')
        
        # VAPI nested structure: body.properties.website.value
        if not website:
            website = request.get('body', {}).get('properties', {}).get('website', {}).get('value', '')
        
        logger.info(f"🔗 VAPI webhook: website={website}")

        # Check for calendar function calls - support multiple VAPI payload formats
        # New format: message.toolCalls (array)
        tool_call_id = None
        tool_calls = request.get('message', {}).get('toolCalls', [])
        if tool_calls and len(tool_calls) > 0:
            # Handle first tool call
            tool_call = tool_calls[0]
            tool_call_id = tool_call.get('id')  # Extract toolCallId
            function_call = tool_call.get('function', {})
            function_name = function_call.get('name')
            parameters = function_call.get('arguments', {})
        else:
            # Old format: functionCall (single)
            function_call = (
                request.get('functionCall', {}) or  # Direct at root
                request.get('message', {}).get('functionCall', {})  # Nested in message
            )
            function_name = function_call.get('name') if function_call else None
            parameters = function_call.get('parameters', {})
            tool_call_id = function_call.get('id') if function_call else None

        if function_name == 'get_availability':
            logger.info("="*80)
            logger.info("📅 CALENDAR FUNCTION: get_availability")
            logger.info(f"📋 Parameters: {json.dumps(parameters, indent=2)}")
            logger.info(f"🔑 User accessing Microsoft Calendar")
            logger.info(f"🆔 Tool Call ID: {tool_call_id}")
            logger.info("="*80)
            result = await calendar_functions.handle_get_availability(parameters)
            logger.info(f"✅ get_availability result:\n{json.dumps(result, indent=2)}")

            # Return VAPI-compliant format with toolCallId
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": result.get("result", "")
                }]
            }

        elif function_name == 'set_appointment':
            logger.info("="*80)
            logger.info("📅 CALENDAR FUNCTION: set_appointment")
            logger.info(f"📋 Parameters: {json.dumps(parameters, indent=2)}")
            logger.info(f"🔑 User creating appointment in Microsoft Calendar")
            logger.info(f"🆔 Tool Call ID: {tool_call_id}")
            logger.info("="*80)
            result = await calendar_functions.handle_set_appointment(parameters)
            logger.info(f"✅ set_appointment result:\n{json.dumps(result, indent=2)}")

            # Return VAPI-compliant format with toolCallId
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": result.get("result", "")
                }]
            }

        # Handle website search
        if website:
            logger.info(f"🔍 Processing website search for: {website}")
            
            if not website:
                return {
                    "detail": [
                        {
                            "type": "error",
                            "loc": ["website"],
                            "msg": "I need a website URL to search for rental properties. Please provide a website.",
                            "input": {
                                "website": ""
                            }
                        }
                    ]
                }
            
            # Check if we have data in the database (prioritize database over freshness)
            stored_rentals = rental_db.get_rentals_for_website(website)
            
            if stored_rentals:
                logger.info(f"✅ Returning {len(stored_rentals)} rentals from database for instant response (bypassing staleness check)")
                
                # Format stored rental data using the same logic as fresh scraping
                domain = website.replace('https://', '').replace('http://', '').split('/')[0]
                response = f"I found {len(stored_rentals)} rental listings for {domain} (from database):\\n\\n"
                
                for i, rental in enumerate(stored_rentals, 1):
                    rental_data = rental["data"]
                    
                    # Address as the top line (main identifier)
                    if 'address' in rental_data:
                        response += f"{i}. {rental_data['address']}\\n"
                    else:
                        response += f"{i}. Rental Property\\n"
                    
                    # Add property type if available
                    if 'property_type' in rental_data:
                        response += f"   Type: {rental_data['property_type'].title()}\\n"
                    
                    # Add price
                    if 'price' in rental_data:
                        response += f"   💰 Rent: {rental_data['price']}\\n"
                    
                    # Add bedrooms and bathrooms
                    if 'bedrooms' in rental_data and 'bathrooms' in rental_data:
                        response += f"   🛏️  {rental_data['bedrooms']} bed, 🚿 {rental_data['bathrooms']} bath\\n"
                    
                    # Add square footage
                    if 'square_feet' in rental_data:
                        response += f"   📏 {rental_data['square_feet']}\\n"
                    
                    # Add availability
                    if 'available_date' in rental_data:
                        response += f"   📅 Available: {rental_data['available_date']}\\n"
                    
                    response += "\\n"
                
                response += "\\n💡 This data was last updated within the day. For real-time updates, the database refreshes automatically daily."
                
                return {
                    "detail": [
                        {
                            "type": "success",
                            "loc": ["rental_search"],
                            "msg": response,
                            "input": {
                                "website": website
                            }
                        }
                    ]
                }
            
            # If no recent data, do the full search and scraping
            logger.info(f"🔍 No recent data found, performing fresh search for: {website}")
            
            try:
                # Import and use the proper DDGS search
                from ddgs import DDGS
                import requests
                from bs4 import BeautifulSoup
                import re
                
                # First, search for rental listings
                search_queries = [
                    f"site:{website} rental properties available",
                    f"site:{website} apartments rent",
                    f"{website} rental listings",
                    f"properties for rent {website.split('//')[1] if '//' in website else website}"
                ]
                
                all_results = []
                
                # Search with multiple strategies
                for query in search_queries:
                    try:
                        with DDGS() as ddgs:
                            results = list(ddgs.text(query, max_results=3))
                            for result in results:
                                if result not in all_results:
                                    all_results.append(result)
                    except Exception as search_error:
                        logger.warning(f"Search query failed: {query} - {search_error}")
                        continue
                
                if all_results:
                    logger.info(f"🔍 Found {len(all_results)} search results from DuckDuckGo, now scraping for details...")
                    
                    # Format DuckDuckGo search results first
                    domain = website.replace('https://', '').replace('http://', '').split('/')[0]
                    duckduckgo_response = f"I found {len(all_results)} listings from DuckDuckGo search for {domain}:\\n\\n"
                    
                    for i, result in enumerate(all_results[:3], 1):
                        title = result.get('title', 'Property listing')
                        snippet = result.get('body', '')
                        duckduckgo_response += f"{i}. {title[:80]}{'...' if len(title) > 80 else ''}\\n"
                        if snippet:
                            duckduckgo_response += f"   {snippet[:100]}...\\n\\n"
                    
                    # Now try to scrape the actual website for detailed rental information using LangChain Playwright Toolkit
                    detailed_listings = []
                    
                    try:
                        logger.info(f"🔍 Using LangChain Playwright Toolkit to scrape: {website}")
                        # Use LangChain Playwright Toolkit for intelligent extraction
                        from langchain_rental_scraper import LangChainRentalScraper
                        scraper = LangChainRentalScraper()
                        detailed_listings = await scraper.scrape_rentals(website)
                        
                        if detailed_listings:
                            logger.info(f"✅ LangChain Playwright Toolkit found {len(detailed_listings)} detailed rental listings")
                            logger.info(f"🔍 LLM Agent Raw Output: {detailed_listings}")
                        else:
                            logger.warning("⚠️ LangChain Playwright Toolkit didn't find detailed rental listings")
                        
                    except Exception as scrape_error:
                        logger.warning(f"LangChain Playwright Toolkit scraping failed: {scrape_error}")
                    
                    # Combine DuckDuckGo results with detailed scraping results
                    if detailed_listings:
                        detailed_response = f"\\n\\n🔍 DETAILED RENTAL INFORMATION (from website scraping):\\n\\n"
                        
                        for i, listing in enumerate(detailed_listings, 1):
                            detailed_response += f"{i}. "
                            
                            # Address as the top line (main identifier)
                            if 'address' in listing:
                                detailed_response += f"{listing['address']}\\n"
                            
                            # Add property type if available
                            if 'property_type' in listing:
                                detailed_response += f"   Type: {listing['property_type'].title()}\\n"
                            
                            # Add price
                            if 'price' in listing:
                                detailed_response += f"   💰 Rent: {listing['price']}\\n"
                            
                            # Add bedrooms and bathrooms
                            if 'bedrooms' in listing and 'bathrooms' in listing:
                                detailed_response += f"   🛏️  {listing['bedrooms']} bed, 🚿 {listing['bathrooms']} bath\\n"
                            
                            # Add square footage
                            if 'square_feet' in listing:
                                detailed_response += f"   📏 {listing['square_feet']}\\n"
                            
                            # Add availability
                            if 'available_date' in listing:
                                detailed_response += f"   📅 Available: {listing['available_date']}\\n"
                            
                            detailed_response += "\\n"
                        
                        detailed_response += "These are the currently available properties with detailed information."
                        
                        # Combine both responses
                        final_response = duckduckgo_response + detailed_response
                        
                    else:
                        # If scraping didn't work, just use DuckDuckGo results
                        final_response = duckduckgo_response + "\\n\\nNote: Couldn't extract detailed rental information from the website, but the search results above show available properties."
                    
                    logger.info(f"✅ Combined search successful for {website}")
                    
                    # Store the rental data in the database for future instant responses
                    if detailed_listings:
                        logger.info(f"💾 Storing {len(detailed_listings)} rental listings in database...")
                        added_count, removed_count = rental_db.sync_rentals(website, detailed_listings)
                        logger.info(f"💾 Database synced: {added_count} rentals added/updated, {removed_count} removed")
                        
                        # Mark database as updated since we just added fresh data
                        rental_db.mark_updated()
                    
                    # Return in VAPI-expected format
                    return {
                        "detail": [
                            {
                                "type": "success",
                                "loc": ["rental_search"],
                                "msg": final_response,
                                "input": {
                                    "website": website
                                }
                            }
                        ]
                    }
                else:
                    # Fallback response
                    domain = website.replace('https://', '').replace('http://', '').split('/')[0]
                    response = f"I wasn't able to find current rental listings for {domain}. The website might not have publicly searchable content, or there may not be available properties right now. I recommend contacting them directly for the most up-to-date availability."
                    
                    return {
                        "detail": [
                            {
                                "type": "warning",
                                "loc": ["rental_search"],
                                "msg": response,
                                "input": {
                                    "website": website
                                }
                            }
                        ]
                    }
                    
            except Exception as e:
                logger.error(f"❌ Website search error: {str(e)}")
                return {
                    "detail": [
                        {
                            "type": "error",
                            "loc": ["rental_search"],
                            "msg": "I'm having trouble searching for rental properties right now. Please try again in a moment.",
                            "input": {
                                "website": website
                            }
                        }
                    ]
                }
        
        # Default response
        return {
            "detail": [
                {
                    "type": "info",
                    "loc": ["general"],
                    "msg": "I can help you search for rental properties on websites. What website would you like me to search?",
                    "input": {}
                }
            ]
        }
        
    except Exception as e:
        return {
            "detail": [
                {
                    "type": "error",
                    "loc": ["system"],
                    "msg": "I'm experiencing technical difficulties. Please try again.",
                    "input": {}
                }
            ]
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
