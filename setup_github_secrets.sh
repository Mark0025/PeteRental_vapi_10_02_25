#!/bin/bash

# GitHub Secrets Setup Script for Docker Hub CI/CD
# This script securely adds Docker Hub credentials to GitHub repository secrets

set -e  # Exit on error

echo "🔐 GitHub Secrets Setup for Docker Hub CI/CD"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository info
REPO="Mark0025/PeteRental_vapi_10_02_25"
DOCKER_USERNAME="mark0025"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install it: brew install gh"
    exit 1
fi

# Check if gh is authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI is not authenticated${NC}"
    echo "Authenticating now..."
    gh auth login
fi

echo -e "${GREEN}✅ GitHub CLI authenticated${NC}"
echo ""

# Check existing secrets
echo -e "${BLUE}📋 Checking existing secrets...${NC}"
EXISTING_SECRETS=$(gh secret list --repo "$REPO" 2>/dev/null || echo "")

if echo "$EXISTING_SECRETS" | grep -q "DOCKER_USERNAME"; then
    echo -e "${YELLOW}⚠️  DOCKER_USERNAME already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping DOCKER_USERNAME"
        SKIP_USERNAME=true
    fi
fi

if echo "$EXISTING_SECRETS" | grep -q "DOCKER_PASSWORD"; then
    echo -e "${YELLOW}⚠️  DOCKER_PASSWORD already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping DOCKER_PASSWORD"
        SKIP_PASSWORD=true
    fi
fi

echo ""

# Add DOCKER_USERNAME
if [ "$SKIP_USERNAME" != true ]; then
    echo -e "${BLUE}📝 Setting DOCKER_USERNAME...${NC}"
    echo "$DOCKER_USERNAME" | gh secret set DOCKER_USERNAME --repo "$REPO"
    echo -e "${GREEN}✅ DOCKER_USERNAME set to: $DOCKER_USERNAME${NC}"
else
    echo -e "${BLUE}⏭️  Skipping DOCKER_USERNAME (already exists)${NC}"
fi

echo ""

# Add DOCKER_PASSWORD
if [ "$SKIP_PASSWORD" != true ]; then
    echo -e "${YELLOW}🔑 Docker Hub Access Token Required${NC}"
    echo ""
    echo "You need to create a Docker Hub access token:"
    echo "1. Visit: https://hub.docker.com/settings/security"
    echo "2. Click 'New Access Token'"
    echo "3. Name: 'GitHub Actions CI/CD'"
    echo "4. Permissions: Read, Write, Delete"
    echo "5. Copy the token"
    echo ""
    echo -e "${RED}⚠️  The token will only be shown once!${NC}"
    echo ""

    # Check if already logged into Docker Hub
    if docker info 2>/dev/null | grep -q "Username"; then
        DOCKER_USER=$(docker info 2>/dev/null | grep "Username" | awk '{print $2}')
        echo -e "${GREEN}✅ You're logged into Docker Hub as: $DOCKER_USER${NC}"
        echo ""
    fi

    read -p "Press Enter when you're ready to paste the token..."
    echo ""

    # Securely read token (won't show in terminal)
    echo -e "${BLUE}Paste your Docker Hub access token:${NC}"
    read -s DOCKER_TOKEN
    echo ""

    # Validate token is not empty
    if [ -z "$DOCKER_TOKEN" ]; then
        echo -e "${RED}❌ Error: Token cannot be empty${NC}"
        exit 1
    fi

    # Add secret to GitHub
    echo "$DOCKER_TOKEN" | gh secret set DOCKER_PASSWORD --repo "$REPO"
    echo -e "${GREEN}✅ DOCKER_PASSWORD set successfully${NC}"

    # Clear token from memory
    unset DOCKER_TOKEN
else
    echo -e "${BLUE}⏭️  Skipping DOCKER_PASSWORD (already exists)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo ""

# Verify secrets
echo -e "${BLUE}📋 Current secrets in repository:${NC}"
gh secret list --repo "$REPO"

echo ""
echo -e "${GREEN}✅ Next steps:${NC}"
echo "1. Secrets are now configured in GitHub"
echo "2. Push your code to trigger CI/CD"
echo "3. Monitor the workflow: https://github.com/$REPO/actions"
echo ""
echo -e "${BLUE}To test the workflow manually:${NC}"
echo "   gh workflow run docker-build-deploy.yml --repo $REPO"
echo ""
