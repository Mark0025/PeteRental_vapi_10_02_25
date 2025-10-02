# PeteRental VAPI - API Documentation

## Quick Start

```bash
# Start the server
./start_dev.sh

# Test endpoints
python3 test_calendar_endpoints.py
```

---

## Calendar Integration Endpoints

### 1. Start OAuth Flow

**Endpoint:** `GET /calendar/auth/start`

**Description:** Initiate Microsoft Calendar OAuth authorization

**Parameters:**
- `user_id` (query, required): Unique identifier for the user

**Example:**
```bash
curl "http://localhost:8000/calendar/auth/start?user_id=user123"
```

**Response:**
```json
{
  "authorization_url": "https://login.microsoftonline.com/...",
  "message": "Visit this URL to authorize calendar access"
}
```

---

### 2. OAuth Callback

**Endpoint:** `GET /calendar/auth/callback`

**Description:** Handle OAuth callback from Microsoft (automatically called by Microsoft)

**Parameters:**
- `code` (query, required): Authorization code from Microsoft
- `state` (query, required): State parameter containing user_id

**Response:**
```json
{
  "status": "success",
  "message": "Calendar connected successfully!",
  "user_id": "user123"
}
```

---

### 3. Check Authorization Status

**Endpoint:** `GET /calendar/auth/status`

**Description:** Check if user has authorized calendar access

**Parameters:**
- `user_id` (query, required): User identifier

**Example:**
```bash
curl "http://localhost:8000/calendar/auth/status?user_id=user123"
```

**Response:**
```json
{
  "authorized": true,
  "expires_at": "2025-10-02T12:00:00"
}
```

---

## VAPI Webhook Endpoint

### Main Webhook Handler

**Endpoint:** `POST /vapi/webhook`

**Description:** Handles all VAPI function calls (rental search and calendar functions)

---

### VAPI Function: `get_availability`

**Description:** Get available viewing times from property manager's calendar

**VAPI Payload:**
```json
{
  "functionCall": {
    "name": "get_availability",
    "parameters": {
      "user_id": "user123",
      "property_address": "123 Main St, Apt 4B"
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "functionCall": {
      "name": "get_availability",
      "parameters": {
        "user_id": "user123",
        "property_address": "123 Main St"
      }
    }
  }'
```

**Response:**
```json
{
  "result": {
    "response": "I have several viewing times available for 123 Main St. Here are the next available slots: Monday, October 2 at 09:00 AM, Monday, October 2 at 10:00 AM, Monday, October 2 at 11:00 AM, Which time works best for you?",
    "available_slots": [
      {
        "start_time": "2025-10-02T09:00:00",
        "end_time": "2025-10-02T09:30:00",
        "duration_minutes": 30,
        "formatted_time": "Monday, October 02 at 09:00 AM"
      }
    ],
    "action": "present_slots"
  }
}
```

---

### VAPI Function: `set_appointment`

**Description:** Book a property viewing appointment

**VAPI Payload:**
```json
{
  "functionCall": {
    "name": "set_appointment",
    "parameters": {
      "user_id": "user123",
      "property_address": "123 Main St, Apt 4B",
      "start_time": "2025-10-02T14:00:00Z",
      "attendee_name": "John Doe",
      "attendee_email": "john@example.com"
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "functionCall": {
      "name": "set_appointment",
      "parameters": {
        "user_id": "user123",
        "property_address": "123 Main St",
        "start_time": "2025-10-02T14:00:00Z",
        "attendee_name": "John Doe",
        "attendee_email": "john@example.com"
      }
    }
  }'
```

**Response:**
```json
{
  "result": {
    "response": "Perfect! I've booked your viewing for 02:00 PM on Monday, October 02 at 123 Main St. You'll receive a calendar invitation shortly. Is there anything else I can help you with?",
    "appointment": {
      "event_id": "AAMkAD...",
      "subject": "Property Viewing - 123 Main St",
      "start_time": "2025-10-02T14:00:00",
      "end_time": "2025-10-02T14:30:00",
      "web_link": "https://outlook.office365.com/..."
    },
    "action": "booked"
  }
}
```

---

## Rental Search Endpoint

### VAPI Function: Rental Website Search

**Description:** Search for rental properties on a specific website

**VAPI Payload:**
```json
{
  "website": "https://nolenpropertiesllc.managebuilding.com"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"website": "https://example-rentals.com"}'
```

**Response:**
```json
{
  "detail": [
    {
      "type": "success",
      "loc": ["rental_search"],
      "msg": "I found 3 rental listings for example-rentals.com...",
      "input": {
        "website": "https://example-rentals.com"
      }
    }
  ]
}
```

---

## Database Endpoints

### Get Database Status

**Endpoint:** `GET /database/status`

**Example:**
```bash
curl http://localhost:8000/database/status
```

**Response:**
```json
{
  "status": "success",
  "database_stats": {
    "total_websites": 2,
    "total_rentals": 15,
    "last_updated": "2025-10-01T10:30:00"
  }
}
```

---

### Get Rentals for Website

**Endpoint:** `GET /database/rentals/{website}`

**Example:**
```bash
curl "http://localhost:8000/database/rentals/nolenrentals.com"
```

---

### Get Available Rentals

**Endpoint:** `GET /database/available`

**Description:** Get all currently available rentals with availability dates

**Example:**
```bash
curl http://localhost:8000/database/available
```

---

## Environment Variables

Required configuration in `.env`:

```bash
# Server
PORT=8000

# OpenRouter API (for rental scraping)
OPENROUTER_API_KEY=sk-or-v1-...

# Microsoft Calendar Integration
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
MICROSOFT_REDIRECT_URI=https://your-domain.com/calendar/auth/callback
```

---

## Testing

### Quick Test Script

```bash
# Test all calendar endpoints
python3 test_calendar_endpoints.py
```

### Manual Testing

1. **Start the server:**
   ```bash
   ./start_dev.sh
   ```

2. **Test health check:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Start OAuth flow:**
   ```bash
   curl "http://localhost:8000/calendar/auth/start?user_id=test123"
   ```

4. **Visit the authorization URL and complete OAuth**

5. **Test VAPI calendar functions:**
   ```bash
   # Get availability
   curl -X POST http://localhost:8000/vapi/webhook \
     -H "Content-Type: application/json" \
     -d '{"functionCall": {"name": "get_availability", "parameters": {"user_id": "test123", "property_address": "123 Main St"}}}'
   ```

---

## Error Responses

### Not Authorized
```json
{
  "result": {
    "response": "You haven't connected your calendar yet. Would you like me to send you an authorization link?",
    "action": "require_auth"
  }
}
```

### Token Expired
```json
{
  "result": {
    "response": "Your calendar authorization expired. Please re-authorize calendar access.",
    "action": "require_auth"
  }
}
```

### Appointment Conflict
```json
{
  "result": {
    "response": "I'm sorry, but 02:00 PM on Monday, October 02 is no longer available. Would you like to check other available times?",
    "action": "conflict"
  }
}
```

---

## Next Steps

1. **Configure Azure App:**
   - Set redirect URI to match `MICROSOFT_REDIRECT_URI`
   - Enable required Microsoft Graph API permissions:
     - `Calendars.ReadWrite`
     - `User.Read`

2. **Deploy to Production:**
   ```bash
   ./deploy.sh
   ```

3. **Update VAPI Configuration:**
   - Set webhook URL to your production endpoint
   - Add `get_availability` and `set_appointment` as custom functions
   - Configure function parameters according to the examples above

---

## Support

For issues or questions, check:
- Main README: `README.md`
- Development docs: `DEV_MAN/README.md`
- Project instructions: `CLAUDE.md`
