# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PeteRental VAPI** is a FastAPI-based rental property search and scraping service that integrates with VAPI (Voice AI Platform). It uses LangChain + OpenRouter for intelligent rental data extraction from property management websites.

## Core Architecture

### Three-Layer Scraping Strategy

1. **DuckDuckGo Search** (`ddgs` library) - Finds rental listing pages across websites
2. **Playwright Scraping** (`playwright_scraper.py`) - Extracts page content from JavaScript-heavy sites
3. **LLM Agent Extraction** (`langchain_rental_scraper.py`) - Uses OpenRouter AI to intelligently parse rental data

### Key Components

- **main.py**: FastAPI application with endpoints for webhook handling, database queries, and health checks
- **langchain_rental_scraper.py**: LangChain-based scraper using Playwright tools and OpenRouter LLM for intelligent extraction
- **rental_database.py**: JSON-based database with intelligent deduplication and daily refresh
- **src/vapi/api/vapi_router.py**: VAPI-specific router for chat completions and webhook handlers

### Database Design

The database uses a unique rental identification system:
- Primary identifier: Property address (most reliable)
- Fallback: Composite key of bedrooms + bathrooms + price
- Auto-syncing: Removes unavailable rentals and adds new ones
- Staleness handling: Returns cached data immediately, refreshes daily in background

## Development Commands

### Local Development

```bash
# Install dependencies
uv sync

# Start development server with ngrok tunnel (hot reload on port 8001)
./start_dev.sh

# Start app only (no ngrok, port 8001)
./start_dev.sh app-only

# Start ngrok tunnel only
./start_dev.sh ngrok-only
```

### Testing

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"website": "https://nolenpropertiesllc.managebuilding.com"}'

# Test LangChain scraper directly
python langchain_rental_scraper.py

# Test rental database
python rental_database.py
```

### Deployment

```bash
# Production deployment with Docker
export OPENROUTER_API_KEY="your_key"
./deploy.sh

# Or use Docker directly
./start_prod.sh

# Deploy to Render (automatic via git push)
git push origin main
```

## Environment Variables

- `OPENROUTER_API_KEY` - **Required** for LLM-powered rental extraction
- `PORT` - Server port (default: 8000)

## API Endpoints

- `GET /` - Server info and status
- `GET /health` - Health check for Render deployment
- `POST /vapi/webhook` - Main webhook handler for VAPI integration
- `GET /database/status` - Database stats and website tracking
- `GET /database/rentals/{website}` - Get rentals for specific website
- `GET /database/available` - Get all available rentals with availability dates

## Important Implementation Details

### Webhook Data Flow

1. Request arrives at `/vapi/webhook` with website parameter
2. Check database for cached rentals (bypass staleness check for instant response)
3. If no cache: DuckDuckGo search → Playwright scraping → LLM extraction
4. Store results in database using `rental_db.sync_rentals()`
5. Return formatted response to VAPI

### LLM Agent Extraction

The `LangChainRentalScraper` uses:
- OpenRouter API (model: `openai/gpt-4o`)
- Playwright async browser for JavaScript-heavy sites
- Structured prompts with explicit rental identification rules
- Fallback to regex extraction if LLM fails

### Deduplication Strategy

Rentals are deduplicated by:
1. Address comparison (primary method)
2. Composite key (bedrooms + bathrooms + price) as fallback
3. Database sync removes unavailable properties automatically

## Deployment Targets

### Render (Recommended)
- Auto-deploys from `main` branch
- Configuration in `render.yaml`
- Docker image: `docker.io/mark0025/peterentalvapi:latest`
- Health check: `/health` endpoint
- Set `OPENROUTER_API_KEY` in Render dashboard

### Docker
- Multi-stage build with Playwright browser support
- Use `docker-compose.yml` for local testing
- Automatic Playwright browser installation in container

## Development Tips

### Testing LLM Extraction

The LLM extraction can be tested independently:
```python
from langchain_rental_scraper import LangChainRentalScraper
import asyncio

scraper = LangChainRentalScraper()
results = asyncio.run(scraper.scrape_rentals("https://example.com"))
```

### Database Management

```python
from rental_database import rental_db

# Get stats
stats = rental_db.get_database_stats()

# Clear old data (7+ days)
rental_db.clear_old_data(days_old=7)

# Sync rentals for a website
added, removed = rental_db.sync_rentals(website, rental_list)
```

### Debugging Webhook Issues

1. Check logs for request structure: `logger.info(f"FULL VAPI REQUEST: {request}")`
2. VAPI sends website in multiple possible locations: direct, body, parameters, functionCall.parameters
3. Database always returns cached data immediately (no staleness check for speed)
4. Fresh scraping happens in background if cache is empty

## Key Libraries

- **FastAPI**: Web framework with async support
- **LangChain**: AI-powered data extraction framework
- **Playwright**: Browser automation for JavaScript-heavy sites
- **OpenRouter**: Multi-model LLM access
- **uv**: Fast Python package manager
- **DDGS**: DuckDuckGo search integration
- **loguru**: Advanced logging
