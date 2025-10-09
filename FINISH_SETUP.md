# Finish Calendar Setup - 3 Manual Steps

I've done the code changes automatically. Now YOU need to do 3 clicks in the Render dashboard:

---

## ✅ What I Did For You
- ✅ Updated `token_manager.py` to use PostgreSQL
- ✅ Added `psycopg2-binary` dependency
- ✅ Committed and pushed to GitHub
- ✅ Render is auto-deploying now (check dashboard)

---

## 🔴 What YOU Need to Do (3 steps, 5 minutes)

### Step 1: Add PostgreSQL Database
1. Go to: https://dashboard.render.com
2. Find your `peterental-vapi` service
3. Click the "PostgreSQL" tab on the left sidebar
4. Click "New PostgreSQL" button
5. Settings:
   - Name: `peterental-tokens` (or whatever you want)
   - Plan: **Starter** (FREE)
   - Region: Same as your service
6. Click "Create Database"
7. **Wait 2 minutes** for it to provision

### Step 2: Link Database to Service
1. Still in Render dashboard
2. Go to your `peterental-vapi` service
3. Click "Environment" tab
4. Click "Add Environment Variable"
5. Add this:
   - Key: `DATABASE_URL`
   - Value: Click "Connect to Database" → Select the database you just created → It auto-fills
6. Click "Save Changes"
7. **Service will redeploy automatically** (takes ~2 minutes)

### Step 3: Authorize Your Calendar
1. Wait for deploy to finish (watch logs)
2. Visit: https://peterentalvapi-latest.onrender.com/calendar/setup
3. Click "Connect Microsoft Calendar"
4. Login with your Microsoft account
5. Accept permissions
6. Done! Token is now saved in PostgreSQL ✅

---

## ✅ Test It Works

```bash
# Should return {"authorized": true}
curl "https://peterentalvapi-latest.onrender.com/calendar/auth/status?user_id=pete_admin"

# Should return available time slots
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "toolCalls": [{
        "function": {
          "name": "get_availability",
          "arguments": {
            "user_id": "pete_admin",
            "property_address": "123 Main St"
          }
        }
      }]
    }
  }'
```

---

## 🎉 After This

Your calendar will:
- ✅ Work in production
- ✅ Persist across redeployments
- ✅ Support 1-20,000 users (when you scale)
- ✅ Work locally too (uses files automatically)

---

## 🆘 If Something Breaks

Check Render logs:
```bash
# In dashboard, click "Logs" tab
# Look for:
"✅ Using PostgreSQL for token storage (persistent)"  ← Good!
"⚠️ PostgreSQL not available"  ← Bad (DATABASE_URL not set)
```

---

**Total Time:** 5 minutes
**Cost:** $0 (free tier)
**What I did:** Code ✅
**What you do:** 3 clicks in Render dashboard

Start here: https://dashboard.render.com
