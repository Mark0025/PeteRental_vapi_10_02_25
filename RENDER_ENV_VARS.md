# Render Environment Variables Setup

## Required Environment Variables for Production

Go to: https://dashboard.render.com → Your Service → Environment Tab

### 1. Core Application
```
PORT=8000
```

### 2. LLM API (for rental scraping)
```
OPENROUTER_API_KEY=your-openrouter-api-key
```

**Get from:** https://openrouter.ai/keys

### 3. Microsoft Calendar OAuth
```
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_TENANT_ID=consumers
MICROSOFT_REDIRECT_URI=https://peterentalvapi-latest.onrender.com/calendar/auth/callback
```

**Get these values from:**
- Azure Portal → App Registrations → Your App → Overview & Certificates & secrets

### 4. PostgreSQL Database
```
DATABASE_URL=[Auto-filled when you connect PostgreSQL database]
```

**How to connect PostgreSQL:**
1. In Render Dashboard → Your Service
2. Click "Environment" tab
3. Click "Add Environment Variable"
4. Key: `DATABASE_URL`
5. Value: Click "Connect to Database" → Select your PostgreSQL instance
6. It auto-fills the connection string

---

## ❌ NOT Needed in Render

- `VAPI_API_KEY` - Only needed for local development to manage VAPI tools
  - Your server receives webhooks from VAPI, doesn't need to call VAPI API

---

## ✅ Current Status

Check which variables are already set in Render:

1. Go to https://dashboard.render.com
2. Select `peterental-vapi` service
3. Click "Environment" tab
4. Verify all variables above are present

**If any are missing, add them using "Add Environment Variable" button**

---

## Testing After Setup

Once all environment variables are set:

1. Service will auto-redeploy (takes ~2 minutes)
2. Check logs for: `✅ Using PostgreSQL for token storage (persistent)`
3. Visit: https://peterentalvapi-latest.onrender.com/calendar/setup
4. Authorize your Microsoft calendar
5. Test VAPI assistant: "Do you have any available viewing times?"

---

## Security Notes

- ✅ `.env` file is in `.gitignore` (credentials not committed to git)
- ✅ Environment variables in Render are encrypted
- ✅ Only accessible to your service
- ✅ Microsoft OAuth credentials are secure
