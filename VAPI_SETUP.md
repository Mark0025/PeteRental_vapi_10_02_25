# VAPI Calendar Integration Setup Guide

## 🎉 Your Calendar is Connected!

Authorization Status: ✅ **Connected** (User: pete_admin)

## 📋 Next Step: Configure VAPI Functions

You need to add two custom functions to your VAPI assistant configuration.

---

## 🔧 VAPI Dashboard Configuration

### 1. Log into VAPI Dashboard
Go to: https://dashboard.vapi.ai

### 2. Select Your Assistant
Navigate to your PeteRental assistant

### 3. Add Custom Functions

Click on **"Functions"** or **"Tools"** section and add these two functions:

---

## Function 1: Get Availability

**Function Name:** `get_availability`

**Description:**
```
Check available viewing times for a property from the property manager's calendar. Returns available time slots for the next 7 days during business hours (9 AM - 5 PM).
```

**Server Configuration:**
- **Type:** `Custom Function` or `HTTP Request`
- **Method:** `POST`
- **URL:** `https://peterentalvapi-latest.onrender.com/vapi/webhook`
  - (Or for testing: `YOUR_NGROK_URL/vapi/webhook`)

**Parameters:**
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "Property manager user ID (use 'pete_admin')",
      "default": "pete_admin"
    },
    "property_address": {
      "type": "string",
      "description": "Full address of the property the caller is interested in"
    }
  },
  "required": ["property_address"]
}
```

**Request Body Template:**
```json
{
  "functionCall": {
    "name": "get_availability",
    "parameters": {
      "user_id": "{{user_id}}",
      "property_address": "{{property_address}}"
    }
  }
}
```

**When to trigger:** When caller asks about:
- "When can I view the property?"
- "What times are available?"
- "Can I schedule a viewing?"
- "When can I see the apartment?"

---

## Function 2: Set Appointment

**Function Name:** `set_appointment`

**Description:**
```
Book a property viewing appointment in the property manager's calendar. Creates a calendar event with the viewing details and sends confirmation.
```

**Server Configuration:**
- **Type:** `Custom Function` or `HTTP Request`
- **Method:** `POST`
- **URL:** `https://peterentalvapi-latest.onrender.com/vapi/webhook`

**Parameters:**
```json
{
  "type": "object",
  "properties": {
    "user_id": {
      "type": "string",
      "description": "Property manager user ID (use 'pete_admin')",
      "default": "pete_admin"
    },
    "property_address": {
      "type": "string",
      "description": "Full address of the property"
    },
    "start_time": {
      "type": "string",
      "description": "Appointment start time in ISO 8601 format (e.g., 2025-10-02T14:00:00Z)"
    },
    "attendee_name": {
      "type": "string",
      "description": "Name of the person viewing the property"
    },
    "attendee_email": {
      "type": "string",
      "description": "Email address of the person viewing the property (optional)"
    }
  },
  "required": ["property_address", "start_time", "attendee_name"]
}
```

**Request Body Template:**
```json
{
  "functionCall": {
    "name": "set_appointment",
    "parameters": {
      "user_id": "{{user_id}}",
      "property_address": "{{property_address}}",
      "start_time": "{{start_time}}",
      "attendee_name": "{{attendee_name}}",
      "attendee_email": "{{attendee_email}}"
    }
  }
}
```

**When to trigger:** When caller wants to:
- "Book a viewing"
- "Schedule an appointment"
- "I'll take the 2 PM slot"
- "Can you book me for Monday at 10 AM?"

---

## 🎯 Assistant Prompt Enhancement

Add this to your VAPI assistant's system prompt:

```
You are a helpful property rental assistant. You can:

1. Search for available rental properties on property management websites
2. Check the property manager's calendar for available viewing times
3. Book property viewing appointments

When a caller expresses interest in viewing a property:
1. First, use get_availability to check available time slots
2. Present 3-5 available times to the caller
3. Once they choose a time, use set_appointment to book it
4. Collect their name and email for the booking
5. Confirm the appointment details

Always be friendly and professional. The property manager's calendar is connected to Microsoft Calendar.
```

---

## 🧪 Testing Your Setup

### Test 1: Check Availability
```bash
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "functionCall": {
      "name": "get_availability",
      "parameters": {
        "user_id": "pete_admin",
        "property_address": "123 Main St, Apt 4B"
      }
    }
  }'
```

**Expected Response:**
```json
{
  "result": {
    "response": "I have several viewing times available for 123 Main St, Apt 4B. Here are the next available slots: Monday, October 02 at 09:00 AM, Monday, October 02 at 10:00 AM, ...",
    "available_slots": [...],
    "action": "present_slots"
  }
}
```

### Test 2: Book Appointment
```bash
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "functionCall": {
      "name": "set_appointment",
      "parameters": {
        "user_id": "pete_admin",
        "property_address": "123 Main St",
        "start_time": "2025-10-02T14:00:00Z",
        "attendee_name": "John Doe",
        "attendee_email": "john@example.com"
      }
    }
  }'
```

**Expected Response:**
```json
{
  "result": {
    "response": "Perfect! I've booked your viewing for 02:00 PM on Monday, October 02 at 123 Main St. You'll receive a calendar invitation shortly.",
    "appointment": {...},
    "action": "booked"
  }
}
```

---

## 🌐 Production Deployment

### Current Setup:
- ✅ Calendar connected (pete_admin)
- ✅ Server running locally
- ✅ Functions ready at `/vapi/webhook`

### For Production:
1. Your Render deployment is already configured at:
   `https://peterentalvapi-latest.onrender.com`

2. Update your production `.env` on Render:
   - Add all Microsoft credentials
   - Set `MICROSOFT_REDIRECT_URI=https://peterentalvapi-latest.onrender.com/calendar/auth/callback`

3. Re-authorize on production:
   - Visit: `https://peterentalvapi-latest.onrender.com/calendar/setup`
   - Complete OAuth flow

4. Update VAPI webhook URL to production:
   `https://peterentalvapi-latest.onrender.com/vapi/webhook`

---

## 🎯 Example Voice Flow

**Caller:** "I'm interested in the apartment on Main Street"

**Assistant:** Uses rental search function to find property

**Caller:** "When can I view it?"

**Assistant:** Calls `get_availability` → "I have several viewing times available. Would you prefer Monday at 10 AM, Monday at 2 PM, or Tuesday at 9 AM?"

**Caller:** "Monday at 2 PM works"

**Assistant:** "Great! Can I get your name and email for the booking?"

**Caller:** "John Doe, john@example.com"

**Assistant:** Calls `set_appointment` → "Perfect! I've booked your viewing for Monday at 2 PM. You'll receive a calendar invitation at john@example.com shortly. Is there anything else I can help you with?"

---

## 📚 Additional Resources

- **API Documentation:** `/API_DOCS.md`
- **Calendar Setup:** `http://localhost:8001/calendar/setup`
- **API Explorer:** `http://localhost:8001/docs`
- **Health Check:** `http://localhost:8001/health`

---

## 🆘 Troubleshooting

### "Not authorized" errors:
- Visit: `http://localhost:8001/calendar/setup`
- Check authorization status
- Re-authorize if needed

### "Invalid token" errors:
- Token may have expired
- Re-authorize via setup page
- Tokens auto-refresh on expiration

### Function not being called:
- Check VAPI function configuration
- Verify webhook URL is correct
- Test endpoint directly with curl

---

## ✅ Checklist

- [x] Calendar connected (pete_admin)
- [ ] Add `get_availability` function to VAPI
- [ ] Add `set_appointment` function to VAPI
- [ ] Update assistant prompt
- [ ] Test with actual voice call
- [ ] Deploy to production (optional)
- [ ] Re-authorize on production

---

**You're all set!** The backend is ready - just need to configure the VAPI dashboard. 🎉
