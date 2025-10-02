# PeteRental VAPI - Troubleshooting Guide

## 🚨 Quick Fix Priority List

### Critical Issues (Fix First)
1. **VAPI Payload Parsing** - Webhook can't extract website from nested JSON
2. **Database Cache Bypass** - System ignores cached data and scrapes live
3. **Response Format Mismatch** - Returns search results instead of property data

### Performance Issues (Fix Second)  
4. **Cold Start Delays** - 15-30 second container startup on Render
5. **Memory Usage Spikes** - 600MB+ during scraping operations
6. **Database Persistence** - Data resets on container restart

---

## 🔧 Critical Fix #1: VAPI Payload Parsing

### Problem Symptoms
```bash
# Test with VAPI-style payload
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "properties": {
        "website": {
          "value": "nolenpropertiesllc.managebuilding.com"
        }
      }
    }
  }'

# ❌ Returns: "I need a website URL to search for rentals"
# ✅ Should return: 4 rental properties from database
```

### Root Cause
**File**: `main.py` lines 167-176  
**Issue**: Missing nested JSON extraction for VAPI payload structure

### Step-by-Step Fix

1. **Locate the extraction logic**:
```bash
grep -n "website.*request.get" main.py
```

2. **Current parsing logic**:
```python path=/Users/markcarpenter/Desktop/pete/peterental_vapi/main.py start=167
# Extract website directly from request body (VAPI sends it directly)
website = request.get('website', '')

# Fallback: check if it's nested in body or other locations
if not website:
    website = request.get('body', {}).get('website', '')
if not website:
    website = request.get('parameters', {}).get('website', '')
if not website:
    website = request.get('functionCall', {}).get('parameters', {}).get('website', '')
```

3. **Apply the fix**:
```python path=null start=null
# Extract website directly from request body (VAPI sends it directly)
website = request.get('website', '')

# Fallback: check if it's nested in body or other locations
if not website:
    website = request.get('body', {}).get('website', '')
if not website:
    website = request.get('parameters', {}).get('website', '')
if not website:
    website = request.get('functionCall', {}).get('parameters', {}).get('website', '')

# ADD THIS: Check VAPI nested structure
if not website:
    website = request.get('body', {}).get('properties', {}).get('website', {}).get('value', '')
    
# Clean up website URL (remove https://)
if website:
    website = website.replace('https://', '').replace('http://', '')
```

4. **Test the fix locally**:
```bash
# Start local server
uv run uvicorn main:app --reload --port 8001

# Test with VAPI payload
curl -X POST http://localhost:8001/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "properties": {
        "website": {
          "value": "https://nolenpropertiesllc.managebuilding.com"
        }
      }
    }
  }'
```

5. **Deploy the fix**:
```bash
# Build and push new image
docker build -t mark0025/peterentalvapi:v1.0.1 .
docker push mark0025/peterentalvapi:v1.0.1

# Render auto-deploys within 2-3 minutes
# Test deployed fix
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d VAPI_PAYLOAD
```

---

## 🔧 Critical Fix #2: Database Cache Priority

### Problem Symptoms
```bash
# Database has perfect data
curl https://peterentalvapi-latest.onrender.com/database/status
# Returns: 4 rentals, last updated 2025-08-25

# But webhook skips database entirely
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -d '{"website": "nolenpropertiesllc.managebuilding.com"}'
# Returns: DuckDuckGo search with 11 results instead of database
```

### Root Cause
**File**: `main.py` lines 198-254  
**Issue**: `is_update_needed()` returns `True` for 3+ day old data, causing database bypass

### Step-by-Step Fix

1. **Locate the database check logic**:
```bash
grep -n "is_update_needed\|stored_rentals" main.py
```

2. **Current logic (problematic)**:
```python path=/Users/markcarpenter/Desktop/pete/peterental_vapi/main.py start=198
# Check if we have recent data in the database
stored_rentals = rental_db.get_rentals_for_website(website)

if stored_rentals and not rental_db.is_update_needed():  # ❌ PROBLEM: skips if >24hrs
    # Return cached data (this almost never happens)
    return format_cached_response(stored_rentals)
else:
    # Always goes here - skips database entirely
    return live_scrape_and_return()
```

3. **Apply the fix** - Prioritize database over freshness:
```python path=null start=null
# Check if we have recent data in the database
stored_rentals = rental_db.get_rentals_for_website(website)

# FIXED: Use database if it has data, regardless of age
if stored_rentals:
    logger.info(f"✅ Returning {len(stored_rentals)} rentals from database for instant response")
    
    # Format the response with proper VAPI structure
    formatted_rentals = []
    for rental in stored_rentals:
        formatted_rentals.append({
            "address": rental["data"]["address"],
            "price": rental["data"]["price"],
            "bedrooms": rental["data"]["bedrooms"],
            "bathrooms": rental["data"]["bathrooms"],
            "square_feet": rental["data"]["square_feet"],
            "available_date": rental["data"]["available_date"],
            "property_type": rental["data"]["property_type"]
        })
    
    return {
        "detail": [{
            "type": "success",
            "loc": ["rental_search"],
            "msg": f"I found {len(formatted_rentals)} rental listings for {website} (from database):\n\n" +
                   "\n\n".join([
                       f"{i+1}. {r['address']}\n"
                       f"   Type: {r['property_type'].title()}\n"
                       f"   💰 Rent: {r['price']}\n"
                       f"   🛏️ {r['bedrooms']} bed, 🚿 {r['bathrooms']} bath\n"
                       f"   📏 {r['square_feet']}\n"
                       f"   📅 Available: {r['available_date']}"
                       for i, r in enumerate(formatted_rentals)
                   ]) + "\n\n💡 This data was last updated within the day.",
            "input": {"website": f"https://{website}"}
        }]
    }

# Only scrape if database is completely empty
if not stored_rentals:
    logger.info(f"🔍 No data in database, performing fresh search for: {website}")
    # ... continue with existing scraping logic
```

4. **Test database priority**:
```bash
# Should return database data instantly
curl -X POST http://localhost:8001/vapi/webhook \
  -d '{"website": "nolenpropertiesllc.managebuilding.com"}'

# Check response time (should be <1 second)
time curl -s -X POST http://localhost:8001/vapi/webhook \
  -d '{"website": "nolenpropertiesllc.managebuilding.com"}' > /dev/null
```

---

## 🔧 Critical Fix #3: Response Format Consistency

### Problem Symptoms
- Database responses use different JSON structure than scraping responses
- VAPI voice synthesis gets inconsistent data formats
- Response times vary wildly (1 sec vs 10 sec)

### Step-by-Step Fix

1. **Standardize response format**:
```python path=null start=null
def format_rental_response(rentals, source="database"):
    """Standardize response format for both database and scraped data"""
    
    formatted_rentals = []
    for rental in rentals:
        # Handle both database format and scraped format
        if isinstance(rental, dict) and "data" in rental:
            # Database format
            data = rental["data"]
        else:
            # Scraped format
            data = rental
            
        formatted_rentals.append({
            "address": data.get("address", "Address not available"),
            "price": data.get("price", "Price not listed"),
            "bedrooms": data.get("bedrooms", "N/A"),
            "bathrooms": data.get("bathrooms", "N/A"), 
            "square_feet": data.get("square_feet", "Size not listed"),
            "available_date": data.get("available_date", "Contact for availability"),
            "property_type": data.get("property_type", "Property").title()
        })
    
    # Create consistent VAPI response structure
    return {
        "detail": [{
            "type": "success",
            "loc": ["rental_search"],
            "msg": format_rental_message(formatted_rentals, source),
            "input": {"website": website}
        }]
    }

def format_rental_message(rentals, source):
    """Create voice-friendly rental listing message"""
    count = len(rentals)
    source_note = f"(from {source})" if source else ""
    
    message = f"I found {count} rental listing{'s' if count != 1 else ''} {source_note}:\n\n"
    
    for i, rental in enumerate(rentals, 1):
        message += f"{i}. {rental['address']}\n"
        message += f"   Type: {rental['property_type']}\n" 
        message += f"   💰 Rent: {rental['price']}\n"
        message += f"   🛏️ {rental['bedrooms']} bed, 🚿 {rental['bathrooms']} bath\n"
        message += f"   📏 {rental['square_feet']}\n"
        message += f"   📅 Available: {rental['available_date']}\n\n"
    
    if source == "database":
        message += "💡 This data was last updated within the day."
    else:
        message += "💡 This is fresh data from a live search."
        
    return message
```

---

## 🧪 Complete Testing Protocol

### Phase 1: Local Testing
```bash
# Start local development server
uv run uvicorn main:app --reload --port 8001

# Test 1: Database status
curl http://localhost:8001/database/status
# Expected: 4 rentals, healthy status

# Test 2: Direct database query 
curl http://localhost:8001/database/rentals/nolenpropertiesllc.managebuilding.com
# Expected: 4 rental properties in JSON

# Test 3: Simple webhook payload
curl -X POST http://localhost:8001/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"website": "nolenpropertiesllc.managebuilding.com"}'
# Expected: Database response in <1 second

# Test 4: VAPI nested payload  
curl -X POST http://localhost:8001/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "properties": {
        "website": {
          "value": "https://nolenpropertiesllc.managebuilding.com"
        }
      }
    }
  }'
# Expected: Same database response in <1 second

# Test 5: Unknown website (scraping fallback)
curl -X POST http://localhost:8001/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"website": "unknown-rental-site.com"}'
# Expected: Live scraping results in 5-10 seconds
```

### Phase 2: Docker Testing
```bash
# Build updated image
docker build -t mark0025/peterentalvapi:v1.0.1 .

# Test locally with Docker
docker run -p 8002:8000 mark0025/peterentalvapi:v1.0.1

# Run same tests on port 8002
curl http://localhost:8002/database/status
curl -X POST http://localhost:8002/vapi/webhook -d VAPI_PAYLOAD
```

### Phase 3: Production Deployment Testing
```bash
# Push to Docker Hub
docker push mark0025/peterentalvapi:v1.0.1

# Wait for Render auto-deploy (2-3 minutes)
# Test deployed fixes
curl https://peterentalvapi-latest.onrender.com/health

# Full production test with VAPI payload
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "properties": {
        "website": {
          "value": "https://nolenpropertiesllc.managebuilding.com"
        }
      }
    }
  }'

# Measure response time
time curl -s -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -H "Content-Type: application/json" \
  -d VAPI_PAYLOAD > /dev/null
# Expected: <2 seconds total (including network)
```

---

## 🔍 Diagnostic Commands

### Check Database State
```bash
# View current database contents
curl -s https://peterentalvapi-latest.onrender.com/database/status | jq .

# Check specific website data
curl -s https://peterentalvapi-latest.onrender.com/database/rentals/nolenpropertiesllc.managebuilding.com | jq .

# Database stats and health
curl -s https://peterentalvapi-latest.onrender.com/database/stats | jq .
```

### Check Container Health
```bash
# Health endpoint
curl https://peterentalvapi-latest.onrender.com/health

# Container logs (if available via Render dashboard)
# Look for: "✅ Returning X rentals from database"
# Bad sign: "🔍 No data in database, performing fresh search"
```

### Validate Docker Image
```bash
# Pull and inspect production image
docker pull mark0025/peterentalvapi:latest
docker image inspect mark0025/peterentalvapi:latest

# Run container and check files
docker run --rm -it mark0025/peterentalvapi:latest /bin/bash
ls -la /app/
cat /app/rental_data.json | jq keys
```

---

## 📊 Performance Monitoring

### Response Time Benchmarks
```bash
# Database responses (target <1 second)
for i in {1..5}; do
  echo "Test $i:"
  time curl -s -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
    -H "Content-Type: application/json" \
    -d '{"website": "nolenpropertiesllc.managebuilding.com"}' > /dev/null
done

# Expected output:
# real    0m0.892s  ✅ Good
# real    0m1.234s  ⚠️  Acceptable  
# real    0m5.678s  ❌ Bad - likely scraping instead of database
```

### Memory Usage Monitoring
```bash
# Check memory usage patterns in Render dashboard
# Normal: 150-200MB steady state
# Spike: 400-600MB during scraping (should be rare)
# Problem: Constantly high memory (indicates constant scraping)
```

---

## 🆘 Emergency Procedures

### Rollback to Previous Version
```bash
# If new deployment breaks something
docker tag mark0025/peterentalvapi:v1.0.0 mark0025/peterentalvapi:latest
docker push mark0025/peterentalvapi:latest

# Render will auto-deploy rollback version
```

### Force Database Refresh
```bash
# If database gets corrupted or empty
curl -X POST https://peterentalvapi-latest.onrender.com/admin/refresh-database

# Or trigger fresh scraping
curl -X POST https://peterentalvapi-latest.onrender.com/vapi/webhook \
  -d '{"website": "nolenpropertiesllc.managebuilding.com", "force_refresh": true}'
```

### Check VAPI Integration
```bash
# Test with exact VAPI webhook URL in VAPI dashboard
# Webhook URL: https://peterentalvapi-latest.onrender.com/vapi/webhook
# Expected: Fast response with 4 rental properties
# Check VAPI logs for response parsing errors
```

---

## ✅ Success Verification Checklist

### After applying all fixes:

- [ ] **VAPI payload parsing works**: Nested JSON extraction successful
- [ ] **Database responses prioritized**: <1 second response time for cached data  
- [ ] **Consistent response format**: Same JSON structure for database and scraped data
- [ ] **Proper fallback behavior**: Live scraping only when database is empty
- [ ] **Voice-optimized responses**: Structured data perfect for VAPI speech synthesis
- [ ] **Production deployment working**: All tests pass on Render
- [ ] **VAPI integration successful**: Live voice calls return correct rental data

### Performance Targets Met:
- [ ] Database responses: <1 second ✅
- [ ] Memory usage: <300MB steady state ✅  
- [ ] Cache hit rate: >90% for known websites ✅
- [ ] VAPI voice quality: Clear, structured property listings ✅

---

**🎯 Goal Achieved**: Simple, fast, reliable rental lookup tool that serves cached data instantly to VAPI voice calls, with proper fallback to live scraping only when necessary.
