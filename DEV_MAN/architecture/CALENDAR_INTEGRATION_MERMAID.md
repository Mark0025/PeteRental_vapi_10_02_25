# Microsoft Calendar Integration - System Architecture

## 🏗️ System Flow Diagram

```mermaid
graph TB
    subgraph "VAPI Voice Agent"
        VA[Voice Agent]
        VW[VAPI Webhook]
    end

    subgraph "FastAPI Application"
        WH[Webhook Handler<br/>/vapi/webhook]
        CF[Calendar Functions<br/>Handler]

        subgraph "Calendar Module"
            OAUTH[OAuth Manager<br/>microsoft_oauth.py]
            CAL[Calendar Manager<br/>microsoft_calendar.py]
            TOKENS[(Token Database<br/>calendar_tokens.json)]
        end

        subgraph "Existing Modules"
            RDB[(Rental Database<br/>rentals.json)]
            SCRAPER[Rental Scraper]
        end
    end

    subgraph "Microsoft Services"
        MSO[Microsoft OAuth 2.0]
        GRAPH[Microsoft Graph API<br/>Calendar Endpoint]
    end

    subgraph "Property Manager"
        PM[Property Manager<br/>Browser]
        PMCAL[Microsoft 365<br/>Calendar]
    end

    %% OAuth Flow
    PM -->|1. Navigate to| WH
    WH -->|2. Redirect to| MSO
    MSO -->|3. User authorizes| PM
    MSO -->|4. Callback with code| OAUTH
    OAUTH -->|5. Exchange code for tokens| MSO
    MSO -->|6. Return access/refresh tokens| OAUTH
    OAUTH -->|7. Store tokens| TOKENS

    %% VAPI Function Call Flow
    VA -->|1. User requests availability| VW
    VW -->|2. POST function call| WH
    WH -->|3. Route to handler| CF
    CF -->|4. Get user token| TOKENS
    CF -->|5. Check availability| CAL
    CAL -->|6. Query calendar| GRAPH
    GRAPH -->|7. Return free/busy data| CAL
    CAL -->|8. Format available slots| CF
    CF -->|9. Return response| WH
    WH -->|10. Send to VAPI| VW
    VW -->|11. Speak to user| VA

    %% Booking Flow
    VA -->|1. User books appointment| VW
    VW -->|2. POST set_appointment| WH
    WH -->|3. Route to handler| CF
    CF -->|4. Get user token| TOKENS
    CF -->|5. Create event| CAL
    CAL -->|6. POST calendar event| GRAPH
    GRAPH -->|7. Create in calendar| PMCAL
    GRAPH -->|8. Confirmation| CAL
    CAL -->|9. Format confirmation| CF
    CF -->|10. Return response| WH
    WH -->|11. Send to VAPI| VW
    VW -->|12. Confirm to user| VA

    style VA fill:#e1f5ff
    style MSO fill:#ff9800
    style GRAPH fill:#ff9800
    style TOKENS fill:#4caf50
    style RDB fill:#4caf50
    style PMCAL fill:#2196f3
```

## 🔄 OAuth Authorization Flow

```mermaid
sequenceDiagram
    participant PM as Property Manager
    participant API as FastAPI App
    participant MS as Microsoft OAuth
    participant DB as Token Database

    Note over PM,DB: Initial Authorization Setup

    PM->>API: GET /calendar/auth/start
    API->>MS: Redirect to Microsoft login
    MS->>PM: Show login page
    PM->>MS: Enter credentials & authorize
    MS->>API: GET /calendar/auth/callback?code=xyz
    API->>MS: POST /oauth2/token (exchange code)
    MS->>API: Return access_token + refresh_token
    API->>DB: Store tokens with user_id
    API->>PM: Success page (tokens stored)

    Note over PM,DB: Token stored and ready for VAPI calls
```

## 📞 VAPI Function Call Flow - get_availability

```mermaid
sequenceDiagram
    participant U as User (Voice)
    participant V as VAPI Agent
    participant API as FastAPI /vapi/webhook
    participant CF as Calendar Functions
    participant DB as Token Database
    participant MS as Microsoft Graph API

    U->>V: "What times are available for viewing?"
    V->>API: POST /vapi/webhook<br/>{functionCall: "get_availability"}
    API->>CF: handle_get_availability(params)
    CF->>DB: get_token(user_id=phone_number)
    DB->>CF: return access_token

    alt Token Expired
        CF->>MS: POST /token (refresh)
        MS->>CF: new access_token
        CF->>DB: update token
    end

    CF->>MS: GET /me/calendar/getSchedule<br/>(next 7 days)
    MS->>CF: return free/busy data
    CF->>CF: filter business hours<br/>format time slots
    CF->>API: return formatted availability
    API->>V: {"result": "Available times are..."}
    V->>U: "We have openings at 10am, 2pm..."
```

## 📅 VAPI Function Call Flow - set_appointment

```mermaid
sequenceDiagram
    participant U as User (Voice)
    participant V as VAPI Agent
    participant API as FastAPI /vapi/webhook
    participant CF as Calendar Functions
    participant DB as Token Database
    participant MS as Microsoft Graph API
    participant CAL as Property Manager Calendar

    U->>V: "Book me for 2pm tomorrow"
    V->>API: POST /vapi/webhook<br/>{functionCall: "set_appointment",<br/>params: {time, property}}
    API->>CF: handle_set_appointment(params)
    CF->>DB: get_token(user_id=phone_number)
    DB->>CF: return access_token

    CF->>MS: GET /me/calendar/getSchedule<br/>(check conflict)
    MS->>CF: return schedule

    alt Time Slot Already Booked
        CF->>API: {"error": "Time unavailable"}
        API->>V: error response
        V->>U: "That time is taken, try another?"
    else Time Slot Available
        CF->>MS: POST /me/calendar/events<br/>(create appointment)
        MS->>CAL: Create calendar event
        MS->>CF: event created confirmation
        CF->>API: {"result": "Appointment confirmed"}
        API->>V: success response
        V->>U: "You're booked for 2pm tomorrow!"
    end
```

## 🗂️ File Structure

```mermaid
graph TB
    subgraph "New Calendar Module"
        CAL_MOD[src/calendar/]
        CAL_MOD --> OAUTH_PY[microsoft_oauth.py<br/>OAuth flow handler]
        CAL_MOD --> CAL_PY[microsoft_calendar.py<br/>Graph API wrapper]
        CAL_MOD --> MODELS_PY[models.py<br/>Pydantic models]
    end

    subgraph "VAPI Functions"
        VAPI_FUNC[src/vapi/functions/]
        VAPI_FUNC --> CAL_FUNC[calendar_functions.py<br/>VAPI function handlers]
    end

    subgraph "Database"
        DATA[data/]
        DATA --> CAL_DB[calendar_tokens.json<br/>OAuth tokens]
        DATA --> RENT_DB[rentals.json<br/>Rental listings]
    end

    subgraph "API Routes"
        MAIN[main.py]
        MAIN --> AUTH_EP[/calendar/auth/*<br/>OAuth endpoints]
        MAIN --> WEBHOOK[/vapi/webhook<br/>Function handler]
    end

    subgraph "Configuration"
        ENV[.env]
        ENV --> MS_CLIENT[MICROSOFT_CLIENT_ID]
        ENV --> MS_SECRET[MICROSOFT_CLIENT_SECRET]
        ENV --> MS_TENANT[MICROSOFT_TENANT_ID]
    end

    OAUTH_PY -.->|reads| MS_CLIENT
    OAUTH_PY -.->|reads| MS_SECRET
    OAUTH_PY -.->|writes| CAL_DB
    CAL_PY -.->|reads| CAL_DB
    CAL_FUNC -.->|uses| CAL_PY
    CAL_FUNC -.->|uses| OAUTH_PY
    WEBHOOK -.->|routes to| CAL_FUNC
    AUTH_EP -.->|uses| OAUTH_PY

    style CAL_MOD fill:#4caf50
    style VAPI_FUNC fill:#2196f3
    style DATA fill:#ff9800
    style ENV fill:#f44336
```

## 🔐 Token Management Flow

```mermaid
stateDiagram-v2
    [*] --> NoToken: Initial State

    NoToken --> Authorizing: User clicks "Connect Calendar"
    Authorizing --> TokenStored: OAuth success
    Authorizing --> AuthFailed: OAuth failed
    AuthFailed --> NoToken: Retry

    TokenStored --> TokenValid: Token check
    TokenValid --> CalendarOperation: Use token
    CalendarOperation --> TokenValid: Success

    TokenValid --> TokenExpired: Token check (60min)
    TokenExpired --> Refreshing: Auto refresh
    Refreshing --> TokenValid: Refresh success
    Refreshing --> AuthFailed: Refresh failed

    CalendarOperation --> RateLimited: API limit hit
    RateLimited --> RetryQueue: Exponential backoff
    RetryQueue --> CalendarOperation: Retry

    TokenStored --> [*]: User revokes
    AuthFailed --> [*]: Give up
```

## 🎯 Data Models

```mermaid
classDiagram
    class CalendarToken {
        +String user_id
        +String access_token
        +String refresh_token
        +DateTime expires_at
        +DateTime created_at
        +DateTime updated_at
        +String calendar_email
        +Boolean is_valid()
        +refresh_if_needed()
    }

    class Availability {
        +String property_address
        +List~TimeSlot~ available_slots
        +DateTime queried_at
        +String timezone
    }

    class TimeSlot {
        +DateTime start_time
        +DateTime end_time
        +Integer duration_minutes
        +String formatted_time
    }

    class Appointment {
        +String event_id
        +String property_address
        +DateTime start_time
        +DateTime end_time
        +String attendee_phone
        +String attendee_email
        +String notes
        +String calendar_link
    }

    class VAPIFunctionCall {
        +String function_name
        +Dict parameters
        +String user_id
        +DateTime timestamp
    }

    CalendarToken "1" --> "*" Availability: queries
    Availability "1" --> "*" TimeSlot: contains
    CalendarToken "1" --> "*" Appointment: creates
    VAPIFunctionCall --> CalendarToken: uses
    VAPIFunctionCall --> Appointment: creates
```

## 🚦 Error Handling Flow

```mermaid
graph TD
    START[VAPI Function Call] --> CHECK_TOKEN{Token Exists?}
    CHECK_TOKEN -->|No| ERROR_NO_AUTH[Return: User not authorized]
    CHECK_TOKEN -->|Yes| CHECK_VALID{Token Valid?}

    CHECK_VALID -->|Expired| REFRESH{Refresh Token?}
    REFRESH -->|Success| CALL_API[Call Microsoft API]
    REFRESH -->|Fail| ERROR_AUTH[Return: Re-authorization needed]

    CHECK_VALID -->|Valid| CALL_API

    CALL_API --> API_RESULT{API Response?}
    API_RESULT -->|Success| FORMAT[Format Response]
    API_RESULT -->|Rate Limit| RETRY[Exponential Backoff]
    API_RESULT -->|Error| ERROR_API[Return: API Error]

    RETRY --> RETRY_COUNT{Retry < 3?}
    RETRY_COUNT -->|Yes| CALL_API
    RETRY_COUNT -->|No| ERROR_TIMEOUT[Return: Service Timeout]

    FORMAT --> RETURN[Return to VAPI]
    ERROR_NO_AUTH --> RETURN
    ERROR_AUTH --> RETURN
    ERROR_API --> RETURN
    ERROR_TIMEOUT --> RETURN

    style START fill:#4caf50
    style RETURN fill:#2196f3
    style ERROR_NO_AUTH fill:#f44336
    style ERROR_AUTH fill:#f44336
    style ERROR_API fill:#f44336
    style ERROR_TIMEOUT fill:#f44336
```

## 📊 Integration Points

```mermaid
graph LR
    subgraph "External Services"
        MS[Microsoft OAuth]
        GRAPH[MS Graph API]
        VAPI[VAPI Platform]
    end

    subgraph "PeteRental API"
        WEBHOOK[Webhook Handler]
        CAL_FUNC[Calendar Functions]
        OAUTH[OAuth Manager]
    end

    subgraph "Storage"
        TOKENS[(Token DB)]
        RENTALS[(Rental DB)]
    end

    VAPI -.->|1. Function Call| WEBHOOK
    WEBHOOK -.->|2. Route| CAL_FUNC
    CAL_FUNC -.->|3. Get Token| TOKENS
    CAL_FUNC -.->|4. Use OAuth| OAUTH
    OAUTH -.->|5. Refresh if needed| MS
    CAL_FUNC -.->|6. Query Calendar| GRAPH
    GRAPH -.->|7. Return Data| CAL_FUNC
    CAL_FUNC -.->|8. Response| WEBHOOK
    WEBHOOK -.->|9. Return| VAPI

    CAL_FUNC -.->|Lookup Property| RENTALS

    style MS fill:#ff9800
    style GRAPH fill:#ff9800
    style VAPI fill:#2196f3
    style TOKENS fill:#4caf50
    style RENTALS fill:#4caf50
```
