# ASKI Plan: Microsoft Calendar OAuth Integration for VAPI

## 🎯 Objective
Add Microsoft Calendar booking capability to PeteRental VAPI so AI agents can check availability and schedule property viewing appointments.

## 📋 A - Assumptions

### Technical Assumptions
1. **OAuth Flow**: Using Microsoft Graph API OAuth 2.0 authorization code flow
2. **Token Storage**: Storing tokens in JSON database (same pattern as rental_database.py)
3. **User Context**: VAPI passes user/caller identification in webhook for token retrieval
4. **Calendar Access**: Property managers grant calendar access via OAuth
5. **Environment**: Same Docker + Render deployment as current app

### Business Assumptions
1. Property managers willing to connect their Microsoft calendars
2. Appointments need 30min - 1hr time slots
3. Standard business hours (9am-5pm) for viewings
4. Same-day bookings should be prevented (24hr minimum notice)

### Integration Assumptions
1. VAPI custom functions support async operations
2. Microsoft Graph API v1.0 is stable for our use case
3. Calendar timezone handling via Microsoft API

## 🧠 S - Strategy

### Phase 1: OAuth Implementation (Priority 1)
**Goal**: Get Microsoft OAuth working with token storage

**Steps**:
1. Create `src/calendar/microsoft_oauth.py` - OAuth flow handler
2. Add OAuth endpoints to FastAPI:
   - `GET /calendar/auth/start` - Redirect to Microsoft login
   - `GET /calendar/auth/callback` - Handle OAuth callback
   - `GET /calendar/auth/status` - Check token status
3. Create `calendar_tokens.json` database for storing access/refresh tokens
4. Implement token refresh logic (tokens expire after 1 hour)

**Success Criteria**:
- User can authorize via browser
- Tokens stored securely in database
- Automatic token refresh working

### Phase 2: Calendar Functions (Priority 1)
**Goal**: Implement availability check and booking

**Steps**:
1. Create `src/calendar/microsoft_calendar.py` - Graph API wrapper
2. Implement `get_availability()` function:
   - Query calendar for free/busy times
   - Return next 7 days of available slots
   - Filter out business hours (9am-5pm)
3. Implement `create_appointment()` function:
   - Create calendar event with property details
   - Send email confirmation to both parties
   - Handle booking conflicts

**Success Criteria**:
- Can fetch calendar availability
- Can create appointments with proper details
- Booking conflicts prevented

### Phase 3: VAPI Function Integration (Priority 1)
**Goal**: Wire calendar functions to VAPI custom functions

**Steps**:
1. Create `src/vapi/functions/calendar_functions.py`
2. Define VAPI function schemas:
   ```json
   {
     "name": "get_availability",
     "parameters": {
       "property_address": "string",
       "user_id": "string"
     }
   }
   ```
3. Add function handlers to `vapi_router.py`
4. Format responses for voice readability

**Success Criteria**:
- VAPI can call get_availability
- VAPI can call set_appointment
- Responses sound natural in voice

### Phase 4: Testing & Documentation (Priority 2)
**Goal**: Ensure reliability and document usage

**Steps**:
1. Create test scripts for OAuth flow
2. Test availability queries with mock calendar
3. Test appointment creation end-to-end
4. Update API docs with calendar endpoints
5. Create setup guide for property managers

## 🔑 K - Key Decisions

### Decision 1: Token Storage
**Options**:
- ✅ **Selected**: JSON file database (consistent with current app)
- ❌ Rejected: PostgreSQL (overkill for MVP)
- ❌ Rejected: Redis (adds infrastructure complexity)

**Rationale**: Keep it simple, follow existing patterns, easy to migrate later

### Decision 2: Calendar Provider
**Options**:
- ✅ **Selected**: Microsoft Graph API only (MVP)
- ❌ Rejected: Google Calendar (add later)
- ❌ Rejected: Multi-provider support (too complex for v1)

**Rationale**: Microsoft 365 is standard in property management, focus on one provider done well

### Decision 3: User Identification
**Options**:
- ✅ **Selected**: VAPI caller phone number as user_id
- ❌ Rejected: Email-based lookup (not available in VAPI webhook)
- ❌ Rejected: Session-based auth (stateless preferred)

**Rationale**: Phone number is unique, available in VAPI webhooks, natural for voice calls

### Decision 4: Appointment Duration
**Options**:
- ✅ **Selected**: Fixed 30min slots
- ❌ Rejected: Variable duration (adds complexity)
- ❌ Rejected: Property-specific duration (not needed yet)

**Rationale**: 30min is industry standard for property viewings, keeps scheduling simple

## 🎬 I - Implementation Plan

### Sprint 1: Core OAuth (Days 1-2)
```
✅ Create branch: feature/calendar-integration
✅ Install dependencies: msal, msgraph-core
✅ Create calendar_tokens.json schema
✅ Implement microsoft_oauth.py
✅ Add OAuth endpoints to main.py
✅ Test OAuth flow manually
```

### Sprint 2: Calendar Operations (Days 3-4)
```
✅ Create microsoft_calendar.py
✅ Implement get_availability() with test data
✅ Implement create_appointment() with validation
✅ Add error handling for token expiry
✅ Test with real Microsoft account
```

### Sprint 3: VAPI Integration (Days 5-6)
```
✅ Create calendar_functions.py
✅ Define function schemas for VAPI
✅ Wire functions to vapi_router.py
✅ Format responses for voice output
✅ Test with VAPI webhook simulator
```

### Sprint 4: Testing & Deploy (Day 7)
```
✅ End-to-end test: OAuth → Availability → Booking
✅ Update FastAPI /docs with calendar endpoints
✅ Test on local Docker
✅ Push to GitHub
✅ Deploy to Render
✅ Verify production endpoints
```

## 📊 Success Metrics

### Technical Metrics
- OAuth flow completes in < 10 seconds
- Availability query responds in < 2 seconds
- Appointment creation confirms in < 3 seconds
- 99% uptime for calendar endpoints

### User Experience Metrics
- Voice agent can successfully:
  1. Check availability and read 3+ time slots
  2. Book appointment with confirmation
  3. Handle "no availability" gracefully
  4. Provide clear error messages

### Integration Metrics
- All VAPI function calls return valid responses
- No token refresh failures
- Calendar conflicts properly detected
- Email confirmations sent 100% of time

## ⚠️ Risks & Mitigations

### Risk 1: Token Expiry During Call
**Impact**: High - User experience broken mid-conversation
**Mitigation**: Pre-check token validity before operations, auto-refresh transparently

### Risk 2: Calendar API Rate Limits
**Impact**: Medium - Some requests may fail
**Mitigation**: Implement exponential backoff, cache availability data for 5min

### Risk 3: Timezone Confusion
**Impact**: Medium - Wrong appointment times booked
**Mitigation**: Always use Microsoft's timezone handling, display timezone in confirmations

### Risk 4: Multi-User Calendar Access
**Impact**: Low - Concurrent booking conflicts
**Mitigation**: Use Microsoft's conflict detection, implement optimistic locking

## 📚 References

- [Microsoft Graph Calendar API](https://learn.microsoft.com/en-us/graph/api/resources/calendar?view=graph-rest-1.0)
- [VAPI Custom Functions](https://docs.vapi.ai/tools/handoff#custom-function-definitions)
- [VAPI Lead Qualification Example](https://docs.vapi.ai/workflows/examples/lead-qualification#calendar-integration)
- [Microsoft OAuth 2.0 Flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)

## 🎯 Definition of Done

- [ ] OAuth flow working end-to-end
- [ ] get_availability returns realistic time slots
- [ ] set_appointment creates calendar events
- [ ] VAPI can call both functions successfully
- [ ] All tests passing
- [ ] API docs updated
- [ ] Deployed to production
- [ ] Property manager setup guide written
