#!/bin/bash

# ZODIRA Backend - Quick Start Script
# This script sets up and runs the ZODIRA unified authentication system

set -e  # Exit on any error

echo "🚀 ZODIRA Backend Quick Start"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Python 3.8+ is installed
check_python() {
    print_step "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.8"
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            print_status "Python $PYTHON_VERSION found ✓"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
}

# Check if Redis is running
check_redis() {
    print_step "Checking Redis connection..."
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_status "Redis is running ✓"
        else
            print_warning "Redis is not running. Starting Redis..."
            if command -v redis-server &> /dev/null; then
                redis-server --daemonize yes
                sleep 2
                if redis-cli ping &> /dev/null; then
                    print_status "Redis started successfully ✓"
                else
                    print_error "Failed to start Redis"
                    exit 1
                fi
            else
                print_error "Redis not installed. Please install Redis server"
                exit 1
            fi
        fi
    else
        print_error "Redis CLI not found. Please install Redis"
        exit 1
    fi
}

# Setup virtual environment
setup_venv() {
    print_step "Setting up virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created ✓"
    else
        print_status "Virtual environment already exists ✓"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_status "Virtual environment activated ✓"
}

# Install dependencies
install_dependencies() {
    print_step "Installing dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Clear pip cache to avoid conflicts
    pip cache purge
    
    print_status "Installing compatible Firebase dependencies..."
    # Install Firebase dependencies first to avoid conflicts
    pip install firebase-admin==6.2.0
    pip install google-cloud-firestore==2.13.1
    pip install google-cloud-storage==2.10.0
    
    print_status "Installing remaining dependencies..."
    # Install remaining dependencies
    pip install -r requirements.txt
    
    # Verify critical imports
    print_step "Verifying installation..."
    python -c "
import fastapi
import firebase_admin
import google.cloud.firestore
import redis
print('✓ All critical dependencies installed successfully')
" || {
        print_error "Dependency verification failed"
        print_warning "Trying alternative installation method..."
        
        # Fallback: Install minimal working set
        pip install fastapi==0.104.1 uvicorn==0.24.0 firebase-admin==6.2.0 redis==5.0.1 python-jose==3.3.0 passlib==1.7.4 httpx==0.25.2 python-decouple==3.8
        
        python -c "from app.main import app; print('✓ Basic application imports working')" || {
            print_error "Critical dependency installation failed"
            print_error "Please check DEPENDENCY_RESOLUTION_GUIDE.md for manual installation steps"
            exit 1
        }
    }
    
    print_status "Dependencies installed and verified ✓"
}

# Setup environment file
setup_env() {
    print_step "Setting up environment configuration..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_status "Environment file created from template ✓"
        print_warning "Please edit .env file with your actual configuration:"
        print_warning "  - Firebase credentials"
        print_warning "  - SMS API keys"
        print_warning "  - Google OAuth credentials"
        print_warning "  - JWT secret key"
        echo ""
        read -p "Press Enter to continue after updating .env file..."
    else
        print_status "Environment file already exists ✓"
    fi
}

# Create required directories
create_directories() {
    print_step "Creating required directories..."
    mkdir -p config
    mkdir -p logs
    print_status "Directories created ✓"
}

# Check Firebase configuration
check_firebase() {
    print_step "Checking Firebase configuration..."
    if [ -f "config/serviceAccountKey.json" ]; then
        print_status "Firebase service account key found ✓"
    else
        print_warning "Firebase service account key not found"
        print_warning "Please download serviceAccountKey.json from Firebase Console"
        print_warning "and place it in config/serviceAccountKey.json"
        echo ""
        read -p "Press Enter to continue after adding Firebase key..."
    fi
}

# Run tests
run_tests() {
    print_step "Running authentication system tests..."
    if python -m pytest tests/test_unified_auth.py -v --tb=short; then
        print_status "All tests passed ✓"
    else
        print_warning "Some tests failed. Check the output above."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Start the application
start_application() {
    print_step "Starting ZODIRA Backend..."
    print_status "Application will be available at: http://localhost:8000"
    print_status "API Documentation: http://localhost:8000/docs"
    print_status "Health Check: http://localhost:8000/api/v1/health"
    print_status "Auth Health Check: http://localhost:8000/api/v1/auth/health"
    echo ""
    print_status "Press Ctrl+C to stop the server"
    echo ""
    
    # Start with uvicorn
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Main execution
main() {
    echo "Starting ZODIRA Backend setup..."
    echo ""
    
    # Run setup steps
    check_python
    check_redis
    setup_venv
    install_dependencies
    setup_env
    create_directories
    check_firebase
    
    # Ask if user wants to run tests
    echo ""
    read -p "Run tests before starting? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        run_tests
    fi
    
    # Start application
    echo ""
    start_application
}

# Handle script arguments
case "${1:-}" in
    "test")
        print_step "Running tests only..."
        source venv/bin/activate 2>/dev/null || true
        run_tests
        ;;
    "setup")
        print_step "Running setup only..."
        check_python
        check_redis
        setup_venv
        install_dependencies
        setup_env
        create_directories
        check_firebase
        print_status "Setup complete! Run './quick_start.sh' to start the server."
        ;;
    "start")
        print_step "Starting application..."
        source venv/bin/activate 2>/dev/null || true
        start_application
        ;;
    *)
        main
        ;;
esac