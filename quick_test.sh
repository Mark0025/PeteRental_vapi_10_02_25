#!/bin/bash

echo "🔄 Re-authorizing calendar..."
AUTH_URL=$(curl -s 'http://localhost:8001/calendar/auth/start?user_id=pete_admin' | python3 -c "import sys, json; print(json.load(sys.stdin)['authorization_url'])")

echo ""
echo "📋 Please visit this URL to re-authorize:"
echo "$AUTH_URL"
echo ""
echo "After authorizing, press ENTER..."
read

echo "✅ Testing calendar function..."
curl -X POST http://localhost:8001/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
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
  }' | python3 -m json.tool
