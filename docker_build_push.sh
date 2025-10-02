#!/bin/bash

echo "🐳 PeteRental VAPI - Build and Push to Docker Hub"
echo "=================================================="

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo "⚠️  Not logged in to Docker Hub. Running docker login..."
    docker login
    if [ $? -ne 0 ]; then
        echo "❌ Docker login failed"
        exit 1
    fi
fi

# Build the image
echo "🔨 Building Docker image..."
docker build -t mark0025/peterentalvapi:latest .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Build successful!"

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
docker push mark0025/peterentalvapi:latest

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to Docker Hub!"
    echo ""
    echo "🎯 Image: mark0025/peterentalvapi:latest"
    echo "🌐 Render will auto-deploy from this image"
    echo ""
    echo "Next steps:"
    echo "1. Render will automatically pull and deploy"
    echo "2. Add Microsoft env vars in Render dashboard:"
    echo "   - MICROSOFT_TENANT_ID=consumers"
    echo "   - MICROSOFT_CLIENT_ID=<your_client_id>"
    echo "   - MICROSOFT_CLIENT_SECRET=<your_client_secret>"
    echo "   - MICROSOFT_REDIRECT_URI=https://peterentalvapi-latest.onrender.com/calendar/auth/callback"
    echo "3. Visit https://peterentalvapi-latest.onrender.com/calendar/setup?user_id=pete_admin"
else
    echo "❌ Push to Docker Hub failed"
    exit 1
fi
