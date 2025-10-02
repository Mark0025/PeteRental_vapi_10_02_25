# PeteRental VAPI

A FastAPI-based rental property search and scraping service that integrates with VAPI (Voice AI Platform) using **LangChain + OpenRouter** for intelligent rental data extraction.

## 🚀 **Features**

- **🤖 LLM Agent**: Uses OpenRouter AI for intelligent rental data extraction
- **🔍 DuckDuckGo Search**: Finds rental listings across websites
- **🌐 Web Scraping**: Playwright-based scraping for JavaScript-heavy sites
- **💾 Smart Database**: JSON storage with intelligent deduplication
- **⏰ Auto Updates**: Daily refresh for fresh rental data
- **🎯 VAPI Integration**: Webhook endpoint for voice AI platforms
- **🐳 Docker Ready**: Production-ready containerization

## 🚀 **Quick Start**

### **Development Mode**

```bash
# Install dependencies
uv sync

# Start development server with ngrok
./start_dev.sh

# Test webhook
curl -X POST http://localhost:8000/vapi/webhook \
  -H "Content-Type: application/json" \
  -d '{"website": "https://nolenpropertiesllc.managebuilding.com"}'
```

### **Production Deployment**

#### **Option 1: Render (Recommended)**

```bash
# Push to GitHub
git add .
git commit -m "Ready for Render deployment"
git push origin main

# Deploy via Render dashboard
# See RENDER_DEPLOYMENT.md for detailed steps
```

#### **Option 2: Docker (Local/Server)**

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY="your_api_key_here"

# Deploy with Docker Compose
./deploy.sh

# Or use Docker directly
./start_prod.sh
```

## 🚀 **Render Deployment (Recommended)**

**Deploy to production in minutes with Render:**

- **render.yaml**: Blueprint for automatic configuration
- **Auto-deploy**: Updates on every git push
- **HTTPS**: Automatically enabled
- **Monitoring**: Built-in logs and metrics
- **Pricing**: Starting at $7/month

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for complete deployment guide.

## 🐳 **Docker Deployment**

The application is also fully containerized for traditional deployment:

- **Dockerfile**: Multi-stage build with Playwright support
- **docker-compose.yml**: Easy deployment with environment variables
- **start_prod.sh**: Production startup script
- **deploy.sh**: Simple deployment script

## 📡 **API Endpoints**

- `GET /` - Server info
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `POST /vapi/webhook` - VAPI webhook handler with LLM-powered rental extraction
- `GET /database/status` - Database statistics
- `GET /database/rentals/{website}` - Get rentals for specific website
- `GET /database/available` - Get available rentals

## 🔧 **Environment Variables**

- `OPENROUTER_API_KEY` - Your OpenRouter API key for LLM agent
- `PORT` - Server port (default: 8000)

## 🏗️ **Architecture**

- **FastAPI**: Modern, fast web framework
- **LangChain**: AI-powered data extraction
- **OpenRouter**: Access to multiple LLM models
- **Playwright**: Robust web scraping
- **uv**: Fast Python dependency management
