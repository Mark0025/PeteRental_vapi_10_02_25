#!/bin/bash

# VAPI API Keys
PRIVATE_KEY="d180ee70-5c20-4d9a-af4f-97f9e1d8957d"
PUBLIC_KEY="d8eb6604-8c1d-4cfa-ae55-c92f7304d1d4"

echo "🔧 Recreating VAPI Calendar Tools"
echo "=================================="

# Delete old tools
echo "🗑️  Deleting old tools..."
curl -s -X DELETE "https://api.vapi.ai/tool/5e89cc10-e066-40d1-884e-6392d93bd624" \
  -H "Authorization: Bearer $PRIVATE_KEY" | jq '.'

curl -s -X DELETE "https://api.vapi.ai/tool/60ea2016-8356-4b07-9dc2-f5a936c88799" \
  -H "Authorization: Bearer $PRIVATE_KEY" | jq '.'

echo ""
echo "✅ Old tools deleted"
echo ""

# Create get_availability tool
echo "📅 Creating get_availability tool..."
TOOL1=$(curl -s -X POST "https://api.vapi.ai/tool" \
  -H "Authorization: Bearer $PRIVATE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "get_availability",
      "description": "Check available viewing times for a property from the property manager'\''s calendar. Returns available time slots for the next 7 days during business hours (9 AM - 5 PM).",
      "parameters": {
        "type": "object",
        "properties": {
          "user_id": {
            "type": "string",
            "description": "Property manager user ID",
            "default": "pete_admin"
          },
          "property_address": {
            "type": "string",
            "description": "Full address of the property the caller is interested in"
          }
        },
        "required": ["property_address"]
      }
    },
    "server": {
      "url": "https://peterentalvapi-latest.onrender.com/vapi/webhook",
      "timeoutSeconds": 20
    },
    "messages": [
      {
        "type": "request-start",
        "content": "Let me check the available viewing times for that property..."
      },
      {
        "type": "request-complete",
        "content": "{{output.result.response}}"
      },
      {
        "type": "request-failed",
        "content": "I'\''m having trouble checking availability right now. Can I help you with something else?"
      }
    ]
  }')

TOOL1_ID=$(echo $TOOL1 | jq -r '.id')
echo "✅ get_availability created: $TOOL1_ID"
echo ""

# Create set_appointment tool
echo "📅 Creating set_appointment tool..."
TOOL2=$(curl -s -X POST "https://api.vapi.ai/tool" \
  -H "Authorization: Bearer $PRIVATE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "set_appointment",
      "description": "Book a property viewing appointment in the property manager'\''s calendar. Creates a calendar event with the viewing details and sends confirmation.",
      "parameters": {
        "type": "object",
        "properties": {
          "user_id": {
            "type": "string",
            "description": "Property manager user ID",
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
    },
    "server": {
      "url": "https://peterentalvapi-latest.onrender.com/vapi/webhook",
      "timeoutSeconds": 20
    },
    "messages": [
      {
        "type": "request-start",
        "content": "Let me book that appointment for you..."
      },
      {
        "type": "request-complete",
        "content": "{{output.result.response}}"
      },
      {
        "type": "request-failed",
        "content": "I couldn'\''t complete the booking right now. Would you like me to take your information and have someone call you back?"
      }
    ]
  }')

TOOL2_ID=$(echo $TOOL2 | jq -r '.id')
echo "✅ set_appointment created: $TOOL2_ID"
echo ""

echo "🎉 Success! New tool IDs:"
echo "  get_availability: $TOOL1_ID"
echo "  set_appointment: $TOOL2_ID"
echo ""
echo "Add these to your VAPI assistant at:"
echo "https://dashboard.vapi.ai/assistants/d8022607-5f25-4091-8582-21f56da6718a"
