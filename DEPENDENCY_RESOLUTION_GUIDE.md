# Dependency Resolution Guide - ZODIRA Backend

## Issue Resolution: Firebase Admin SDK Compatibility

### Problem
The original requirements.txt had conflicting dependencies between `firebase-admin==7.1.0` and `google-cloud-firestore==2.11.1` which caused installation failures.

### Solution
Updated to compatible versions that work together:

```
firebase-admin==6.2.0          # Stable version with proven compatibility
google-cloud-firestore==2.13.1 # Compatible with firebase-admin 6.2.0
```

## Updated Requirements.txt

### Core Dependencies (Tested & Compatible)
```
# Core Framework
fastapi==0.104.1               # Stable FastAPI version
uvicorn[standard]==0.24.0      # Compatible ASGI server

# Firebase and Google Cloud (Compatible versions)
firebase-admin==6.2.0          # Stable Firebase Admin SDK
google-cloud-firestore==2.13.1 # Compatible Firestore client
google-cloud-storage==2.10.0   # Google Cloud Storage

# Data Validation
pydantic==2.5.0               # Stable Pydantic v2
pydantic-settings==2.1.0      # Settings management

# Authentication & Security
python-jose[cryptography]==3.3.0  # JWT handling
passlib[bcrypt]==1.7.4            # Password hashing
google-auth==2.23.4               # Google OAuth
```

### Production Dependencies
```
# Performance & Caching
redis==5.0.1                  # Session management
gunicorn==21.2.0              # Production WSGI server

# Monitoring & Logging
prometheus-client==0.19.0     # Metrics collection
python-json-logger==2.0.7     # Structured logging
structlog==23.2.0             # Advanced logging

# Security & Rate Limiting
slowapi==0.1.9               # Rate limiting middleware
```

## Installation Instructions

### Method 1: Clean Installation (Recommended)
```bash
# Remove existing virtual environment
rm -rf venv

# Create fresh virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip to latest version
pip install --upgrade pip

# Install dependencies in order
pip install -r requirements.txt
```

### Method 2: Force Reinstall
```bash
# Activate existing environment
source venv/bin/activate

# Force reinstall all packages
pip install --force-reinstall -r requirements.txt
```

### Method 3: Step-by-Step Installation
```bash
# Install core dependencies first
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0

# Install Firebase dependencies
pip install firebase-admin==6.2.0
pip install google-cloud-firestore==2.13.1
pip install google-cloud-storage==2.10.0

# Install remaining dependencies
pip install -r requirements.txt
```

## Verification Commands

### Check Installation Success
```bash
# Verify core packages
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import firebase_admin; print(f'Firebase Admin: {firebase_admin.__version__}')"
python -c "import google.cloud.firestore; print('Firestore: OK')"
python -c "import redis; print('Redis: OK')"

# Test application imports
python -c "from app.main import app; print('Application imports: OK')"
python -c "from app.services.unified_auth_service import unified_auth_service; print('Auth service: OK')"
```

### Check for Conflicts
```bash
# Check for dependency conflicts
pip check

# List installed packages
pip list

# Show dependency tree
pip install pipdeptree
pipdeptree
```

## Alternative Installation Methods

### Using Poetry (Recommended for Development)
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Initialize Poetry project
poetry init

# Add dependencies
poetry add fastapi==0.104.1
poetry add firebase-admin==6.2.0
poetry add google-cloud-firestore==2.13.1
# ... add other dependencies

# Install
poetry install

# Activate environment
poetry shell
```

### Using Conda
```bash
# Create conda environment
conda create -n zodira python=3.9

# Activate environment
conda activate zodira

# Install pip packages
pip install -r requirements.txt
```

### Using Docker (Isolation)
```bash
# Build Docker image with dependencies
docker build -t zodira-backend .

# Run container
docker run -p 8000:8000 zodira-backend
```

## Troubleshooting Common Issues

### Issue 1: Version Conflicts
**Error**: `ERROR: Cannot install package-a and package-b because these package versions have conflicting dependencies`

**Solution**:
```bash
# Clear pip cache
pip cache purge

# Use dependency resolver
pip install --use-feature=2020-resolver -r requirements.txt

# Or install with no dependencies first, then resolve
pip install --no-deps -r requirements.txt
pip install -r requirements.txt
```

### Issue 2: Compilation Errors
**Error**: `Failed building wheel for package-name`

**Solution**:
```bash
# Install build tools
pip install wheel setuptools

# For macOS, install Xcode command line tools
xcode-select --install

# For Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# Retry installation
pip install -r requirements.txt
```

### Issue 3: SSL Certificate Errors
**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**:
```bash
# Upgrade certificates
pip install --upgrade certifi

# For macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# Retry installation
pip install -r requirements.txt
```

### Issue 4: Permission Errors
**Error**: `Permission denied` during installation

**Solution**:
```bash
# Use user installation
pip install --user -r requirements.txt

# Or fix permissions
sudo chown -R $USER ~/.local/lib/python3.x/site-packages/
```

## Production Deployment

### Docker Production Build
```dockerfile
# Use Python 3.9 slim image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Production Requirements Validation
```bash
# Test production installation
docker build -t zodira-test .
docker run --rm zodira-test python -c "
import fastapi
import firebase_admin
import google.cloud.firestore
import redis
print('All dependencies working correctly')
"
```

## Version Compatibility Matrix

| Package | Version | Compatible With |
|---------|---------|-----------------|
| firebase-admin | 6.2.0 | google-cloud-firestore 2.13.1 |
| google-cloud-firestore | 2.13.1 | firebase-admin 6.2.0 |
| fastapi | 0.104.1 | pydantic 2.5.0 |
| pydantic | 2.5.0 | fastapi 0.104.1 |
| redis | 5.0.1 | All versions |
| python-jose | 3.3.0 | All versions |

## Quick Fix Commands

### If Installation Still Fails
```bash
# Emergency fix: Install without version constraints
pip install firebase-admin google-cloud-firestore --no-deps
pip install -r requirements.txt --no-deps
pip install fastapi uvicorn redis python-jose passlib

# Verify basic functionality
python -c "from app.main import app; print('Basic imports working')"
```

### Minimal Working Set
If you need to get running quickly with minimal dependencies:
```bash
pip install fastapi==0.104.1 uvicorn==0.24.0 firebase-admin==6.2.0 redis==5.0.1 python-jose==3.3.0 passlib==1.7.4 httpx==0.25.2 python-decouple==3.8
```

This dependency resolution ensures all packages work together without conflicts while maintaining the full functionality of the unified authentication system.