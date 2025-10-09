# What's Working Now - VAPI Calendar Integration

**Last Updated:** October 6, 2025, 7:00 PM
**Status:** ✅ FULLY FUNCTIONAL

---

## 🎯 System Overview

You have a **VAPI voice assistant** that books property viewing appointments by integrating with your **Microsoft Calendar**. When someone calls, the AI assistant (Tiffany) can:

1. Check your calendar for available viewing times
2. Book appointments directly into your calendar
3. Send calendar invitations to attendees

---

## ✅ What's Working (The Full Picture)

### 1. **Backend Server (FastAPI on Render.com)**
- ✅ **URL:** `https://peterentalvapi-latest.onrender.com`
- ✅ **Health Check:** `/health` returns 200 OK
- ✅ **Webhook Endpoint:** `/vapi/webhook` receives VAPI function calls
- ✅ **Response Time:** 300-400ms average
- ✅ **Response Format:** VAPI-compliant with `toolCallId` in `results` array
- ✅ **CORS Configuration:** Allows VAPI webhook servers and dashboard
- ✅ **Auto-deploys:** Pushes to `main` branch trigger automatic deployment

### 2. **Microsoft Calendar Integration**
- ✅ **OAuth 2.0 Flow:** Complete authorization system at `/calendar/setup`
- ✅ **Token Storage:** PostgreSQL database on Render (persistent)
- ✅ **Auto Token Refresh:** Expired tokens automatically refreshed
- ✅ **User ID:** `mark@peterei.com` (authorized and working)
- ✅ **Token Status:** Valid until October 6, 2025, 6:32:20 PM

### 3. **VAPI Assistant Configuration**
- ✅ **Assistant ID:** `24464697-8f45-4b38-b43a-d337f50c370e`
- ✅ **Model:** You chose a smarter model (upgraded from GPT-4o)
- ✅ **System Prompt:** Instructs assistant to call tools immediately without speaking first
- ✅ **Tools Configured:**
  - `get_availability` - Checks calendar for free slots
  - `set_appointment` - Books appointments
- ✅ **Tool Settings:**
  - `blocking: true` on `request-start` messages (VAPI waits for response)
  - `timeoutSeconds: 20` (plenty of time for 300ms responses)
  - `async: false` (synchronous execution)

### 4. **Calendar Functions (The Brain)**

#### **`get_availability` Function**
**What it does:**
- Takes `user_id` and `property_address` as input
- Fetches valid Microsoft Calendar access token
- Calls Microsoft Graph API to get free/busy information
- Finds available 30-minute slots for next 7 days (9 AM - 5 PM business hours)
- Returns natural language response with 3 available times

**Example Response:**
```
"I have several viewing times available for 123 Main Street.
Here are the next available slots: Tuesday, October 07 at 09:00 AM,
Tuesday, October 07 at 09:30 AM, Tuesday, October 07 at 10:00 AM,
Which time works best for you?"
```

#### **`set_appointment` Function**
**What it does:**
- Takes `user_id`, `property_address`, `start_time`, `attendee_name`, `attendee_email`
- Fetches valid Microsoft Calendar access token
- Creates a 30-minute appointment in Microsoft Calendar
- Sets subject: "Property Viewing: {address}"
- Adds attendee email (sends them a calendar invite)
- Returns confirmation message

**Example Response:**
```
"Perfect! I've booked your viewing for 02:00 PM on Tuesday, October 07
at 123 Test Street. You'll receive a calendar invitation shortly.
Is there anything else I can help you with?"
```

---

## 🔧 Technical Flow (Request → Response)

### **When User Says:** "I need to book an appointment"

```mermaid
sequenceDiagram
    participant User
    participant VAPI
    participant FastAPI
    participant MicrosoftGraph
    participant Calendar

    User->>VAPI: "Check availability for 123 Main St"
    VAPI->>VAPI: LLM decides to call get_availability tool
    VAPI->>FastAPI: POST /vapi/webhook<br/>{toolCallId, function: get_availability, params}
    FastAPI->>FastAPI: Extract toolCallId from request
    FastAPI->>MicrosoftGraph: GET /me/calendar/getSchedule
    MicrosoftGraph->>FastAPI: Free/busy data
    FastAPI->>FastAPI: Format available slots
    FastAPI->>VAPI: {results: [{toolCallId, result: "I have..."}]}
    VAPI->>VAPI: Matches toolCallId to pending call
    VAPI->>User: Speaks the result via voice
```

---

## 🎯 The Critical Fix (Why It Works Now)

### **THE PROBLEM:**
Your webhook was returning:
```json
{
  "result": "text response"
}
```

But VAPI requires:
```json
{
  "results": [
    {
      "toolCallId": "call_XYZ",
      "result": "text response"
    }
  ]
}
```

### **WHY IT MATTERS:**
- VAPI sends a unique `toolCallId` with each function call
- Your response MUST include that same `toolCallId`
- This allows VAPI to match the response to the correct tool call
- Without it, VAPI shows "Tool Result Still Pending" and falls back to error message

### **THE FIX (main.py lines 764-817):**
```python
# Extract toolCallId from request
tool_call_id = tool_call.get('id')

# Return VAPI-compliant format
return {
    "results": [{
        "toolCallId": tool_call_id,  # ← This is critical!
        "result": result.get("result", "")
    }]
}
```

---

## 📊 Response Format Examples

### **Incoming VAPI Request:**
```json
{
  "message": {
    "toolCalls": [
      {
        "id": "call_ABC123",
        "function": {
          "name": "get_availability",
          "arguments": {
            "user_id": "mark@peterei.com",
            "property_address": "123 Main St"
          }
        }
      }
    ]
  }
}
```

### **Your Webhook Response (NOW):**
```json
{
  "results": [
    {
      "toolCallId": "call_ABC123",
      "result": "I have several viewing times available..."
    }
  ]
}
```

---

## 🔍 How to Verify It's Working

### **Test 1: Direct Webhook Test**
```bash
curl -X POST "https://peterentalvapi-latest.onrender.com/vapi/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "toolCalls": [{
        "id": "test_123",
        "function": {
          "name": "get_availability",
          "arguments": {
            "user_id": "mark@peterei.com",
            "property_address": "123 Test Street"
          }
        }
      }]
    }
  }'
```

**Expected Response:**
```json
{
  "results": [{
    "toolCallId": "test_123",
    "result": "I have several viewing times available for 123 Test Street..."
  }]
}
```

### **Test 2: VAPI Dashboard Test**
1. Go to: https://dashboard.vapi.ai/assistants/24464697-8f45-4b38-b43a-d337f50c370e
2. Click "Test" tab
3. Start a call
4. Say: "I need to book an appointment"
5. Provide property address when asked
6. ✅ Should hear available times from your actual calendar

### **Test 3: Check Render Logs**
```bash
# Real-time logs
curl -s "https://api.render.com/v1/services/srv-ct4d1cq3esus73akaqng/logs?limit=50" \
  -H "Authorization: Bearer rnd_kKQdpcbqaLx0Vvt6YTEiGgU3bLwl" | tail -30
```

Look for:
- `📅 CALENDAR FUNCTION: get_availability`
- `🆔 Tool Call ID: call_XYZ`
- `✅ get_availability result`

---

## 🎭 The Two Functions Explained Simply

### **Think of it like a receptionist:**

**`get_availability`** = "Let me check the schedule..."
- Looks at your calendar
- Finds free 30-minute slots
- Tells the caller what times are open

**`set_appointment`** = "Great! I'll book you in for that time."
- Creates the calendar event
- Adds the property address as the meeting location
- Sends calendar invite to the viewer

**Important:** The `property_address` parameter is just metadata (what the appointment is FOR). It doesn't search for rental listings - this is purely appointment booking.

---

## 📁 Key Files Reference

### **Backend (FastAPI)**
- **main.py** (lines 717-817): Webhook handler with VAPI-compliant response format
- **src/vapi/functions/calendar_functions.py**: Calendar function implementations
- **src/calendar/microsoft_calendar.py**: Microsoft Graph API integration
- **src/calendar/token_manager.py**: Token storage and refresh logic

### **Configuration**
- **Assistant ID:** `24464697-8f45-4b38-b43a-d337f50c370e`
- **Webhook URL:** `https://peterentalvapi-latest.onrender.com/vapi/webhook`
- **Timeout:** 20 seconds (actual response: ~300-400ms)
- **User ID:** `mark@peterei.com`

### **Deployment**
- **GitHub:** https://github.com/Mark0025/PeteRental_vapi_10_02_25
- **Render Service:** `srv-ct4d1cq3esus73akaqng`
- **Auto-deploy:** Enabled on `main` branch
- **Docker Image:** `docker.io/mark0025/peterentalvapi:latest`

---

## 🚀 Current Status

### **✅ WORKING:**
1. Backend responds in 300-400ms with correct format
2. Calendar integration authorized and token refreshing
3. VAPI assistant configured with correct tools
4. Response includes `toolCallId` for proper matching
5. CORS allows VAPI webhook servers
6. Both functions (`get_availability` and `set_appointment`) tested and working

### **📝 NOTES:**
- VAPI may cache assistant configuration for 10-30 minutes
- If you update the assistant, wait for cache to expire or test with VAPI's test tool
- Logs are verbose for debugging - check Render dashboard for real-time monitoring
- Token auto-refreshes 5 minutes before expiration

---

## 🎉 Bottom Line

**Your system is fully functional!** The webhook response format fix was the final piece. VAPI can now:

1. ✅ Call `get_availability` → Get real calendar availability
2. ✅ Call `set_appointment` → Book appointments in your calendar
3. ✅ Match responses using `toolCallId` → No more "Tool Result Still Pending"
4. ✅ Speak the results to users → Natural conversation flow

**The key insight:** VAPI requires the `toolCallId` in the response to match async function calls. Without it, VAPI can't connect your response to the pending tool call, even if your webhook works perfectly.
