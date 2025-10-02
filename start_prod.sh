#!/bin/bash

# Production startup script for PeteRental VAPI
echo "=================================="
echo "  PeteRental VAPI Production"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t peterental-vapi:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker image built successfully!"

# Run the container
echo "🚀 Starting production container..."
docker run -d \
    --name peterental-vapi-prod \
    -p 8000:8000 \
    -e PORT=8000 \
    -e OPENROUTER_API_KEY="${OPENROUTER_API_KEY}" \
    --restart unless-stopped \
    peterental-vapi:latest

if [ $? -ne 0 ]; then
    echo "❌ Failed to start container!"
    exit 1
fi

echo "✅ Production container started successfully!"
echo ""
echo "🌐 Application is running at: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🔍 VAPI webhook: http://localhost:8000/vapi/webhook"
echo ""
echo "📋 Container logs: docker logs peterental-vapi-prod"
echo "🛑 Stop container: docker stop peterental-vapi-prod"
echo "🗑️  Remove container: docker rm peterental-vapi-prod"
