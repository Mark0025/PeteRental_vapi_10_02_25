#!/bin/bash

# Simple deployment script for PeteRental VAPI
echo "=================================="
echo "  PeteRental VAPI Deployment"
echo "=================================="

# Check if OPENROUTER_API_KEY is set
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY environment variable is not set!"
    echo "Please set it: export OPENROUTER_API_KEY='your_key_here'"
    exit 1
fi

echo "✅ OPENROUTER_API_KEY is set"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

echo "🚀 Starting deployment..."

# Build and start the services
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Application is running at: http://localhost:8000"
    echo "📚 API docs: http://localhost:8000/docs"
    echo "🔍 VAPI webhook: http://localhost:8000/vapi/webhook"
    echo ""
    echo "📋 View logs: docker-compose logs -f"
    echo "🛑 Stop: docker-compose down"
    echo "🔄 Restart: docker-compose restart"
else
    echo "❌ Deployment failed!"
    exit 1
fi
