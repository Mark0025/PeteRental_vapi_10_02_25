#!/bin/bash

# Simple Docker Build and Push Script
# Use this until GitHub Actions billing is resolved

set -e

echo "🐳 PeteRental VAPI - Docker Build & Deploy"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Run tests first
echo "🧪 Running tests..."
uv run python -c "from rental_database import rental_db; print(f'✅ Database: {rental_db.get_database_stats()}')"
uv run python -c "from main import app; print('✅ FastAPI app loaded')"
echo ""

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t mark0025/peterentalvapi:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Build successful!"
echo ""

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
docker push mark0025/peterentalvapi:latest

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully deployed!"
    echo ""
    echo "🎯 Image: mark0025/peterentalvapi:latest"
    echo "🌐 Render will auto-deploy in 2-3 minutes"
    echo ""
    echo "📊 Verify deployment:"
    echo "   curl https://peterentalvapi-latest.onrender.com/health"
else
    echo "❌ Push failed"
    exit 1
fi
