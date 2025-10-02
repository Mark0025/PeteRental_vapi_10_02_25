# PeteRental VAPI - Full Architecture Analysis

## Current Architecture Diagram

```mermaid
graph TB
    subgraph "End Users"
        A[Voice User via VAPI]
        B[Browser User]
    end

    subgraph "Frontend - Vercel"
        C[Next.js 15 App]
        C1[Home Page]
        C2[Calendar Page]
        C3[VAPI Testing Page]
        C4[Users Page]
        C --> C1
        C --> C2
        C --> C3
        C --> C4
    end

    subgraph "Backend - Render.com"
        D[FastAPI Python Server]
        D1[VAPI Webhook Handler]
        D2[Calendar Endpoints]
        D3[Rental Database]
        D4[LangChain Scraper]
        D --> D1
        D --> D2
        D --> D3
        D --> D4
    end

    subgraph "External Services"
        E[Microsoft Graph API]
        F[VAPI Platform]
        G[OpenRouter LLM]
        H[Property Websites]
    end

    subgraph "Deployment Pipeline"
        I[GitHub Actions]
        J[Docker Hub]
        K[Render Auto-Deploy]
        L[Vercel Auto-Deploy]
    end

    A -->|Voice Commands| F
    F -->|Webhook POST| D1
    D1 -->|Function Calls| D2

    B -->|HTTPS| C
    C -->|API Calls| D2

    D2 -->|OAuth + API Calls| E
    D4 -->|Scrape| H
    D4 -->|LLM| G

    I -->|Build & Push| J
    J -->|Pull Image| K
    K -->|Deploy| D

    I -->|Build & Deploy| L
    L -->|Deploy| C

    style A fill:#e1f5ff
    style B fill:#e1f5ff
    style C fill:#c3e6cb
    style D fill:#ffeaa7
    style F fill:#ff7675
    style E fill:#74b9ff
```

## THE REAL ISSUE

**Root Cause**: Render backend has NOT been deployed with the latest code that includes CORS middleware.

**Why "Failed to fetch"**: The production backend is running an OLD Docker image without:
- CORS headers allowing Vercel domain
- `/calendar/events` endpoint
- Updated error handling

**The Fix**: Manual deployment on Render dashboard

## Deployment Complexity Explained

### GitHub Actions → Docker Hub → Render (Current)
1. Code pushed to GitHub
2. GitHub Actions builds Docker image
3. Image pushed to Docker Hub as `mark0025/peterentalvapi:latest`
4. **Render MUST manually pull the new image** ⚠️

This is NOT automated because Render is configured to use a pre-built Docker image, not build from source.

### Alternative: Direct GitHub → Render
- Render could build directly from GitHub
- Slower deploys (Playwright install takes time)
- Would be fully automatic

## Should We Migrate to Next.js Only?

### NO - Keep Current Architecture

**Reasons**:
1. ✅ Python backend works well for:
   - VAPI webhooks
   - LangChain rental scraping
   - Playwright browser automation
   
2. ✅ Next.js frontend perfect for:
   - User interface
   - Testing tools
   - OAuth redirect pages

3. ✅ Separation of concerns is GOOD:
   - Frontend: UI/UX
   - Backend: Business logic, APIs, data processing

4. ✅ Current issue is just deployment config
   - Not an architecture problem
   - Just need to trigger Render deployment

## The Real Problem & Solution

### Problem
**Render requires manual deployment trigger** when using pre-built Docker images from Docker Hub.

### Solution Options

**Option 1: Manual Deploy (Quick Fix - Do This Now)**
1. Go to Render dashboard
2. Click "Manual Deploy" → "Deploy latest commit"
3. Wait 2-3 minutes
4. Test again - should work

**Option 2: Automate Render Deployment (Long-term)**
Add a step to GitHub Actions that triggers Render deployment via API:

```yaml
- name: Trigger Render Deploy
  run: |
    curl -X POST https://api.render.com/deploy/srv-XXXXX?key=YOUR_DEPLOY_KEY
```

**Option 3: Change Render to Build from GitHub (Slower)**
- Configure Render to build directly from GitHub repo
- Automatic deploys, but slower (5-7 min vs 2-3 min)

## Current Status

✅ Frontend: Working, deployed, correct env vars
⚠️ Backend: Docker image built, pushed to Docker Hub, **NOT deployed to Render yet**
🔧 Action Needed: Manual deploy on Render dashboard

After you deploy on Render, everything will work.
