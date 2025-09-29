# Troubleshooting Startup Issues - ZODIRA Backend

## Issue Resolution Guide

### ✅ **RESOLVED: Pydantic Validation Error**
**Error**: `ValidationError: secret_key - Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]`

**Root Cause**: The `SECRET_KEY` environment variable was not set, causing Pydantic to receive `None` instead of a string.

**Solution Applied**:
1. Updated [`app/config/settings.py`](app/config/settings.py:25) to provide a secure default value
2. Changed `DEBUG` to `APP_DEBUG` to avoid conflict with system `DEBUG=WARN` environment variable
3. Updated [`.env`](.env:3) and [`.env.example`](.env.example:3) files accordingly

### ✅ **RESOLVED: Boolean Validation Error**
**Error**: `ValueError: Invalid truth value: warn`

**Root Cause**: System environment variable `DEBUG=WARN` was conflicting with application's boolean `DEBUG` setting.

**Solution Applied**:
- Renamed application debug setting from `DEBUG` to `APP_DEBUG`
- Updated configuration files to use the new variable name

### 🔧 **CURRENT ISSUE: Missing Dependencies**
**Error**: `ModuleNotFoundError: No module named 'jose'`

**Root Cause**: Dependencies not installed in virtual environment.

**Solution Steps**:

#### Step 1: Activate Virtual Environment
```bash
# Navigate to project directory
cd /Users/devjay/Development/zodira_backend

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
which python
which pip
```

#### Step 2: Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install compatible Firebase dependencies first
pip install firebase-admin==6.2.0
pip install google-cloud-firestore==2.13.1

# Install all dependencies
pip install -r requirements.txt

# Verify critical imports
python -c "
import fastapi
import firebase_admin
import google.cloud.firestore
import redis
from jose import jwt
print('✓ All dependencies installed successfully')
"
```

#### Step 3: Test Application Import
```bash
# Test configuration loading
python -c "from app.config.settings import settings; print('✓ Settings loaded')"

# Test application import
python -c "from app.main import app; print('✓ Application imported successfully')"
```

#### Step 4: Start Application
```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Quick Fix Commands

### If Virtual Environment Issues Persist
```bash
# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Install minimal working dependencies
pip install --upgrade pip
pip install fastapi==0.104.1 uvicorn==0.24.0
pip install firebase-admin==6.2.0
pip install python-jose[cryptography]==3.3.0
pip install passlib[bcrypt]==1.7.4
pip install python-decouple==3.8
pip install redis==5.0.1
pip install httpx==0.25.2

# Test basic functionality
python -c "from app.main import app; print('✓ Basic setup working')"
```

### Alternative: Use the Quick Start Script
```bash
# Make script executable
chmod +x quick_start.sh

# Run automated setup
./quick_start.sh setup

# Then start application
./quick_start.sh start
```

## Environment Variable Validation

### Check Current Environment Variables
```bash
# Check for conflicting variables
env | grep DEBUG
env | grep SECRET

# Check application-specific variables
python -c "
from app.config.settings import settings
print(f'Environment: {settings.environment}')
print(f'Debug: {settings.debug}')
print(f'Secret Key Length: {len(settings.secret_key)}')
print(f'Firebase Project: {settings.firebase_project_id}')
"
```

### Required Environment Variables
Ensure these are set in your `.env` file:
```env
# Critical for startup
ENVIRONMENT=development
APP_DEBUG=false
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars-zodira-2024

# Firebase (update with your values)
FIREBASE_SERVICE_ACCOUNT_PATH=config/serviceAccountKey.json
FIREBASE_PROJECT_ID=zodira-23a77
FIREBASE_STORAGE_BUCKET=zodira-23a77.appspot.com

# SMS API
MYDREAMS_API_KEY=zbAG4xSPKhwqPCI3
MYDREAMS_SENDER_ID=MYDTEH

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Dependency Installation Troubleshooting

### Issue: Firebase Admin SDK Conflicts
```bash
# Install specific compatible versions
pip uninstall firebase-admin google-cloud-firestore -y
pip install firebase-admin==6.2.0
pip install google-cloud-firestore==2.13.1
```

### Issue: SSL/TLS Warnings
**Warning**: `urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'`

**Solution** (macOS):
```bash
# Install OpenSSL via Homebrew
brew install openssl

# Reinstall Python packages with proper SSL
pip install --upgrade --force-reinstall urllib3
```

### Issue: Compilation Errors
```bash
# Install build tools (macOS)
xcode-select --install

# Install build tools (Ubuntu/Debian)
sudo apt-get install build-essential python3-dev

# Retry installation
pip install -r requirements.txt
```

## Startup Verification Commands

### Step-by-Step Verification
```bash
# 1. Check Python environment
python --version
which python

# 2. Check virtual environment
echo $VIRTUAL_ENV

# 3. Check critical imports
python -c "import fastapi; print('FastAPI OK')"
python -c "import firebase_admin; print('Firebase OK')"
python -c "from jose import jwt; print('JWT OK')"
python -c "import redis; print('Redis OK')"

# 4. Check application configuration
python -c "from app.config.settings import settings; print('Config OK')"

# 5. Check application import
python -c "from app.main import app; print('App OK')"

# 6. Start application
uvicorn app.main:app --reload
```

## Success Indicators

### Application Started Successfully
When the application starts correctly, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Auth health check
curl http://localhost:8000/api/v1/auth/health

# API documentation
# Open browser: http://localhost:8000/docs
```

## Next Steps After Successful Startup

### 1. Test Authentication Flow
```bash
# Test email authentication
curl -X POST "http://localhost:8000/api/v1/auth/initiate" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test@example.com"}'
```

### 2. Configure External Services
- Set up Firebase service account key
- Configure SMS provider credentials
- Set up Google OAuth credentials
- Configure Redis server

### 3. Run Comprehensive Tests
```bash
# Run authentication tests
pytest tests/test_unified_auth.py -v

# Run all tests
pytest tests/ -v
```

This troubleshooting guide addresses the specific startup issues encountered and provides clear resolution steps.