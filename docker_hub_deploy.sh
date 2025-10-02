#!/bin/bash

echo "🐳 PeteRental VAPI - Docker Hub Deployment"
echo "=========================================="

# Pull latest image from Docker Hub
echo "📥 Pulling latest image from Docker Hub..."
docker pull mark0025/peterentalvapi:latest

# Stop any existing container
echo "🛑 Stopping existing container..."
docker stop peterental-vapi 2>/dev/null || true
docker rm peterental-vapi 2>/dev/null || true

# Run new container from Docker Hub
echo "🚀 Starting container from Docker Hub..."
docker run -d \
  --name peterental-vapi \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  mark0025/peterentalvapi:latest

# Wait for startup
echo "⏳ Waiting for container startup..."
sleep 5

# Check health
echo "🔍 Checking container health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Container deployed successfully!"
    echo "🌐 API: http://localhost:8000"
    echo "📚 Docs: http://localhost:8000/docs"
    echo "🎯 VAPI webhook: http://localhost:8000/vapi/webhook"
else
    echo "❌ Container health check failed"
    echo "📋 Container logs:"
    docker logs peterental-vapi
fi
