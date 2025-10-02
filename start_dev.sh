#!/bin/bash

# Pete Rental VAPI Development Start Script
# This script starts ngrok and the FastAPI application in development mode

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_PORT=8000
NGROK_PORT=4040
DEV_PORT=8001
NGROK_URL=""  # Global variable to store ngrok URL

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Pete Rental VAPI Dev Script${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to kill processes on a port
kill_port() {
    if port_in_use $1; then
        print_warning "Port $1 is in use. Killing existing processes..."
        lsof -ti :$1 | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

# Function to start ngrok
start_ngrok() {
    if ! command_exists ngrok; then
        print_error "ngrok is not installed. Please install it first:"
        print_error "  brew install ngrok/ngrok/ngrok (macOS)"
        print_error "  Or download from: https://ngrok.com/download"
        exit 1
    fi
    
    # Determine which port to forward based on mode
    local forward_port=$1
    print_status "Starting ngrok tunnel on port $forward_port..."
    
    # Kill any existing ngrok processes
    pkill -f ngrok || true
    
    # Start ngrok in background
    ngrok http $forward_port > /dev/null 2>&1 &
    NGROK_PID=$!
    
    # Wait for ngrok to start and get URL
    print_status "Waiting for ngrok to initialize..."
    local attempts=0
    local max_attempts=10
    
    while [ $attempts -lt $max_attempts ] && [ -z "$NGROK_URL" ]; do
        sleep 2
        attempts=$((attempts + 1))
        
        # Try to get ngrok URL (ngrok v3 API)
        if command_exists jq; then
            NGROK_URL=$(curl -s http://localhost:$NGROK_PORT/api/tunnels 2>/dev/null | jq -r '.tunnels[0].public_url' 2>/dev/null)
        else
            NGROK_URL=$(curl -s http://localhost:$NGROK_PORT/api/tunnels 2>/dev/null | grep -o '"public_url":"[^"]*"' | cut -d'"' -f4 2>/dev/null)
        fi
        
        # Also try the ngrok v3 edge API
        if [ -z "$NGROK_URL" ] || [ "$NGROK_URL" = "null" ]; then
            NGROK_URL=$(curl -s http://localhost:$NGROK_PORT/api/edge/tls/endpoints 2>/dev/null | jq -r '.endpoints[0].hostname' 2>/dev/null)
            if [ ! -z "$NGROK_URL" ] && [ "$NGROK_URL" != "null" ]; then
                NGROK_URL="https://$NGROK_URL"
            fi
        fi
        
        print_status "Attempt $attempts/$max_attempts: Waiting for ngrok..."
    done
    
    if [ ! -z "$NGROK_URL" ] && [ "$NGROK_URL" != "null" ]; then
        print_status "✅ ngrok tunnel started successfully!"
        print_status "🔗 Local ngrok dashboard: http://localhost:$NGROK_PORT"
    else
        print_warning "Could not get ngrok URL automatically, but ngrok may still be running"
        print_status "🔗 Check ngrok dashboard: http://localhost:$NGROK_PORT"
        print_status "🌐 You can manually copy the public URL from the dashboard"
        print_status "📋 Add '/vapi/webhook' to the ngrok URL for VAPI testing"
    fi
}

# Function to start the application in development mode
start_dev_app() {
    print_status "Starting FastAPI application in development mode on port $DEV_PORT..."
    
    # Kill any existing processes on dev port
    kill_port $DEV_PORT
    
    # Check if uv is available
    if command_exists uv; then
        print_status "Using uv for development with hot reload..."
        # Use uv to run uvicorn with reload
        uv run uvicorn main:app --host 0.0.0.0 --port $DEV_PORT --reload &
    else
        print_status "Using uvicorn directly..."
        uvicorn main:app --host 0.0.0.0 --port $DEV_PORT --reload &
    fi
    
    DEV_APP_PID=$!
    sleep 3
    
    if port_in_use $DEV_PORT; then
        print_status "✅ Development app started successfully!"
        print_status "🚀 Dev server: http://localhost:$DEV_PORT"
        print_status "📚 API docs: http://localhost:$DEV_PORT/docs"
    else
        print_error "Failed to start development app"
        exit 1
    fi
}

# Function to start the application in regular mode
start_regular_app() {
    print_status "Starting FastAPI application in regular mode on port $APP_PORT..."
    
    # Kill any existing processes on app port
    kill_port $APP_PORT
    
    # Check if uv is available
    if command_exists uv; then
        print_status "Using uv for regular mode..."
        # Use uv to run uvicorn
        uv run uvicorn main:app --host 0.0.0.0 --port $APP_PORT &
    else
        print_status "Using uvicorn directly..."
        uvicorn main:app --host 0.0.0.0 --port $APP_PORT &
    fi
    
    REGULAR_APP_PID=$!
    sleep 3
    
    if port_in_use $APP_PORT; then
        print_status "✅ Regular app started successfully!"
        print_status "🚀 App server: http://localhost:$APP_PORT"
        print_status "📚 API docs: http://localhost:$APP_PORT/docs"
    else
        print_error "Failed to start regular app"
        exit 1
    fi
}

# Function to display VAPI webhook URL prominently
display_webhook_url() {
    if [ ! -z "$NGROK_URL" ] && [ "$NGROK_URL" != "null" ]; then
        echo ""
        echo -e "${BLUE}================================${NC}"
        echo -e "${BLUE}  🚀 VAPI WEBHOOK READY!${NC}"
        echo -e "${BLUE}================================${NC}"
        echo -e "${GREEN}$NGROK_URL/vapi/webhook${NC}"
        echo -e "${BLUE}================================${NC}"
        echo -e "${YELLOW}📋 Copy this URL and paste it into VAPI for testing!${NC}"
        echo -e "${YELLOW}💡 In VAPI: Tools → Add Tool → Webhook → Paste URL above${NC}"
        echo ""
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up processes..."
    
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$DEV_APP_PID" ]; then
        kill $DEV_APP_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$REGULAR_APP_PID" ]; then
        kill $REGULAR_APP_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "uv run" 2>/dev/null || true
    pkill -f ngrok 2>/dev/null || true
    
    print_status "Cleanup complete!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM EXIT

# Main script
main() {
    print_header
    
    # Check if we're in the right directory
    if [ ! -f "main.py" ]; then
        print_error "main.py not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Check Python dependencies
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check if we're in a virtual environment or if uv is available
    if command_exists uv; then
        print_status "✅ uv is available - will use it to manage dependencies"
        # Check if dependencies are installed
        if ! uv run python -c "import fastapi, uvicorn" 2>/dev/null; then
            print_warning "Some dependencies may not be installed. Run 'uv sync' to install them."
        fi
    else
        print_warning "uv not found - will use system Python packages"
    fi
    
    # Parse command line arguments
    MODE=${1:-dev}
    
    case $MODE in
        "dev"|"development")
            print_status "Starting in DEVELOPMENT mode..."
            start_ngrok $DEV_PORT
            start_dev_app
            
            print_status "🎉 Development environment is ready!"
            print_status "Press Ctrl+C to stop all services"
            
            # Final display of webhook URL
            sleep 1
            display_webhook_url
            
            # Keep script running
            wait
            ;;
            
        "regular"|"prod"|"production")
            print_status "Starting in REGULAR mode..."
            start_ngrok $APP_PORT
            start_regular_app
            
            print_status "🎉 Regular environment is ready!"
            print_status "Press Ctrl+C to stop all services"
            
            # Final display of webhook URL
            sleep 1
            display_webhook_url
            
            # Keep script running
            wait
            ;;
            
        "ngrok-only")
            print_status "Starting ngrok only..."
            start_ngrok $APP_PORT
            
            print_status "🎉 ngrok tunnel is ready!"
            print_status "Press Ctrl+C to stop ngrok"
            
            # Keep script running
            wait
            ;;
            
        "app-only")
            print_status "Starting app only (no ngrok)..."
            start_dev_app
            
            print_status "🎉 App is ready!"
            print_status "Press Ctrl+C to stop the app"
            
            # Keep script running
            wait
            ;;
            
        *)
            print_error "Invalid mode: $MODE"
            echo "Usage: $0 [dev|regular|ngrok-only|app-only]"
            echo ""
            echo "Modes:"
            echo "  dev (default)     - Start ngrok + app in development mode with hot reload"
            echo "  regular           - Start ngrok + app in regular mode"
            echo "  ngrok-only        - Start only ngrok tunnel"
            echo "  app-only          - Start only app in development mode"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
