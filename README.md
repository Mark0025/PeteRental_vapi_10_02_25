# PeteRental VAPI - Property Management Voice AI

A FastAPI-based platform integrating VAPI (Voice AI Platform) with Microsoft Calendar for intelligent appointment booking and property management.

## 🚀 **Core Features**

### **Primary: Appointment Booking System**
- **📅 Microsoft Calendar Integration**: OAuth 2.0 flow with auto-refresh tokens
- **🎙️ VAPI Voice Agent**: Natural language appointment scheduling
- **📞 get_availability**: Check calendar for available viewing times
- **📝 set_appointment**: Book property viewings with calendar invites
- **👥 Multi-User Support**: PostgreSQL token storage for multiple users

### **Secondary: Rental Property Search**
- **🤖 LLM-Powered Scraping**: LangChain + OpenRouter for intelligent extraction
- **🔍 DuckDuckGo Search**: Finds rental listings across websites
- **🌐 Playwright Scraping**: JavaScript-heavy site support
- **💾 Smart Caching**: JSON database with deduplication

### **Infrastructure**
- **🐳 Docker Ready**: Multi-stage production builds
- **☁️ Render Deployment**: Auto-deploy on git push
- **🔐 Secure OAuth**: Microsoft Graph API integration
- **📊 PostgreSQL Storage**: Production-ready database

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

See [deployment/RENDER_DEPLOYMENT.md](DEV_MAN/deployment/RENDER_DEPLOYMENT.md) for complete deployment guide.

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

## 📚 **Documentation**

All technical documentation is organized in the `DEV_MAN/` directory:

### **Overview & Planning**
- [COMPLETE_SYSTEM_ANALYSIS.md](DEV_MAN/COMPLETE_SYSTEM_ANALYSIS.md) - Full system analysis with diagrams and roadmap
- [EXECUTIVE_SUMMARY.md](DEV_MAN/EXECUTIVE_SUMMARY.md) - Quick reference guide
- [WORKFLOW_SUMMARY.md](DEV_MAN/WORKFLOW_SUMMARY.md) - Development workflow
- [PROJECT_MASTER.md](DEV_MAN/PROJECT_MASTER.md) - Master project plan

### **Deployment** ([DEV_MAN/deployment/](DEV_MAN/deployment/))
- [RENDER_DEPLOYMENT.md](DEV_MAN/deployment/RENDER_DEPLOYMENT.md) - Render deployment guide
- [RENDER_ENV_VARS.md](DEV_MAN/deployment/RENDER_ENV_VARS.md) - Environment variables
- [DEPLOYMENT_PIPELINE.md](DEV_MAN/deployment/DEPLOYMENT_PIPELINE.md) - CI/CD pipeline

### **Guides** ([DEV_MAN/guides/](DEV_MAN/guides/))
- [USING_AGENT_SYSTEM.md](DEV_MAN/guides/USING_AGENT_SYSTEM.md) - **Multi-agent system quick reference**
- [DATABASE_MIGRATIONS.md](DEV_MAN/guides/DATABASE_MIGRATIONS.md) - Database migration system
- [VAPI_SETUP.md](DEV_MAN/guides/VAPI_SETUP.md) - VAPI configuration
- [FINISH_SETUP.md](DEV_MAN/guides/FINISH_SETUP.md) - Setup completion
- [FIX_CALENDAR_QUICK.md](DEV_MAN/guides/FIX_CALENDAR_QUICK.md) - Calendar troubleshooting
- [CLEANUP_SUMMARY.md](DEV_MAN/guides/CLEANUP_SUMMARY.md) - Code cleanup notes

### **Reference** ([DEV_MAN/reference/](DEV_MAN/reference/))
- [API_DOCS.md](DEV_MAN/reference/API_DOCS.md) - API documentation
- [WHATS_WORKING.md](DEV_MAN/reference/WHATS_WORKING.md) - Current working features

### **Architecture** ([DEV_MAN/architecture/](DEV_MAN/architecture/))
- [VAPI_NETWORK_ANALYSIS.md](DEV_MAN/architecture/VAPI_NETWORK_ANALYSIS.md) - Network diagrams
- [CALENDAR_INTEGRATION_ASKI.md](DEV_MAN/architecture/CALENDAR_INTEGRATION_ASKI.md) - ASCII diagrams
- [CALENDAR_INTEGRATION_MERMAID.md](DEV_MAN/architecture/CALENDAR_INTEGRATION_MERMAID.md) - Mermaid diagrams

### **Development**
- [README.md](DEV_MAN/README.md) - DEV_MAN documentation index
- [troubleshooting.md](DEV_MAN/troubleshooting.md) - Common issues and solutions

## 🐛 **Issues & Development**

- **GitHub Issues**: Track bugs and features at [Issues](https://github.com/Mark0025/PeteRental_vapi_10_02_25/issues)
- **Current Branch**: `feature/organize-and-multi-agent-setup`
- **Multi-Agent Roadmap**: See [COMPLETE_SYSTEM_ANALYSIS.md](DEV_MAN/COMPLETE_SYSTEM_ANALYSIS.md)

## 🤝 **Contributing**

See [WORKFLOW_SUMMARY.md](DEV_MAN/WORKFLOW_SUMMARY.md) for development workflow and git practices.
