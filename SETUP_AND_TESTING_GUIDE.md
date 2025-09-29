# ZODIRA Unified Authentication System - Setup and Testing Guide

## Prerequisites Setup

### 1. System Requirements
- **Python 3.8+** (recommended: Python 3.9 or 3.10)
- **Redis Server** (local or remote instance)
- **Firebase Project** with Authentication enabled
- **Git** for version control

### 2. Environment Setup
```bash
# Clone the repository
git clone <repository-url>
cd zodira_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your actual configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables:**
```env
# Environment Configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-super-secure-secret-key-min-32-chars

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000

# MyDreams SMS API Configuration
SMS_PROVIDER=mydreams
MYDREAMS_API_URL=http://app.mydreamstechnology.in/vb/apikey.php
MYDREAMS_API_KEY=zbAG4xSPKhwqPCI3
MYDREAMS_SENDER_ID=MYDTEH
ZODIRA_SUPPORT_EMAIL=support@zodira.app

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=config/serviceAccountKey.json
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_STORAGE_BUCKET=your-firebase-project-id.appspot.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Database and Redis Setup

### 1. Redis Server Setup

**Option A: Local Redis Installation**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS (using Homebrew)
brew install redis
brew services start redis

# Windows (using WSL or Docker)
docker run -d -p 6379:6379 redis:7-alpine
```

**Option B: Redis Cloud/Remote**
```bash
# Update REDIS_URL in .env file
REDIS_URL=redis://username:password@host:port/database
```

**Verify Redis Connection:**
```bash
redis-cli ping
# Should return: PONG
```

### 2. Firebase Setup

**Step 1: Create Firebase Project**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project or select existing
3. Enable Authentication service
4. Enable Firestore Database

**Step 2: Download Service Account Key**
1. Go to Project Settings → Service Accounts
2. Generate new private key
3. Save as `config/serviceAccountKey.json`

**Step 3: Configure Authentication Methods**
1. In Firebase Console → Authentication → Sign-in method
2. Enable Email/Password authentication
3. Enable Google authentication (optional)

### 3. Database Initialization

**Create Required Directories:**
```bash
mkdir -p config
mkdir -p logs
```

**Initialize Firestore Collections:**
The application will automatically create collections on first use:
- `users` - User profiles and authentication data
- `auth_sessions` - Authentication sessions (if not using Redis)
- `user_profiles` - Extended user profile information

## Running the Application

### 1. Development Server
```bash
# Start development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative with more verbose logging
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### 2. Production Server
```bash
# Install production server
pip install gunicorn

# Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With custom configuration
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --log-level info
```

### 3. Docker Deployment
```bash
# Build Docker image
docker build -t zodira-backend .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f zodira-backend
```

### 4. Verify Application Startup
```bash
# Check health endpoint
curl http://localhost:8000/api/v1/health

# Check authentication service health
curl http://localhost:8000/api/v1/auth/health

# Access interactive API documentation
# Open browser: http://localhost:8000/docs
```

## Testing Authentication Flows

### 1. Interactive API Documentation
Access the Swagger UI at `http://localhost:8000/docs` for interactive testing.

### 2. Email Authentication Flow

**Step 1: Initiate Email Authentication**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "test@example.com"
  }'
```

**Expected Response:**
```json
{
  "session_id": "abc123...",
  "auth_type": "email",
  "status": "otp_sent",
  "message": "OTP sent to your email address",
  "expires_in": 300,
  "next_step": "verify_otp"
}
```

**Step 2: Verify OTP (Check logs for OTP in development)**
```bash
# Check application logs for OTP
tail -f logs/app.log | grep "EMAIL OTP"

# Verify OTP
curl -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123...",
    "otp_code": "123456"
  }'
```

### 3. Phone Authentication Flow

**Step 1: Initiate Phone Authentication**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/initiate" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "+1234567890"
  }'
```

**Step 2: Verify SMS OTP**
```bash
# OTP will be sent via SMS to the phone number
# In development mode, check logs for OTP
tail -f logs/app.log | grep "SMS OTP"

# Verify OTP
curl -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_id_from_step1",
    "otp_code": "received_otp"
  }'
```

### 4. Google OAuth Flow

**Step 1: Get Google ID Token (Client-side)**
```javascript
// Frontend JavaScript example
const response = await gapi.auth2.getAuthInstance().signIn();
const idToken = response.getAuthResponse().id_token;
```

**Step 2: Authenticate with Backend**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/google-oauth" \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "google_id_token_from_client"
  }'
```

### 5. Test Protected Endpoints
```bash
# Use JWT token from authentication response
JWT_TOKEN="your_jwt_token_here"

curl -X GET "http://localhost:8000/api/v1/profiles" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Running Test Suite

### 1. Install Test Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov httpx faker
```

### 2. Run Authentication System Tests
```bash
# Run unified authentication tests
pytest tests/test_unified_auth.py -v

# Run with detailed output
pytest tests/test_unified_auth.py -v -s

# Run specific test
pytest tests/test_unified_auth.py::TestUnifiedAuthService::test_initiate_auth_email -v
```

### 3. Run Full Test Suite
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# Run tests with specific markers
pytest tests/ -m "auth" -v
```

### 4. Test Specific Authentication Flows
```bash
# Test email authentication flow
pytest tests/test_unified_auth.py::test_email_authentication_flow -v

# Test phone authentication flow
pytest tests/test_unified_auth.py::test_phone_authentication_flow -v

# Test Google OAuth flow
pytest tests/test_unified_auth.py::test_google_oauth_flow -v

# Test rate limiting
pytest tests/test_unified_auth.py::test_rate_limiting -v
```

### 5. Performance Testing
```bash
# Install performance testing tools
pip install locust

# Run load tests
locust -f tests/load_test_auth.py --host=http://localhost:8000
```

## Monitoring and Debugging

### 1. Application Metrics
```bash
# Access Prometheus metrics
curl http://localhost:8000/metrics

# Key metrics to monitor:
# - request_count_total
# - request_duration_seconds
# - auth_attempts_total
# - otp_sent_total
# - auth_success_rate
```

### 2. Application Logs
```bash
# Monitor application logs
tail -f logs/app.log

# Filter authentication events
tail -f logs/app.log | grep "AUTH"

# Monitor error logs
tail -f logs/app.log | grep "ERROR"

# Monitor OTP delivery
tail -f logs/app.log | grep "OTP"
```

### 3. Redis Monitoring
```bash
# Connect to Redis CLI
redis-cli

# Monitor Redis operations
redis-cli monitor

# Check authentication sessions
redis-cli keys "auth_session:*"

# Check rate limiting
redis-cli keys "auth_rate_limit:*"
```

### 4. SMS Provider Monitoring
```bash
# Check SMS delivery logs
curl -X GET "http://app.mydreamstechnology.in/vb/delivery_report.php" \
  -G -d "apikey=zbAG4xSPKhwqPCI3"

# Monitor SMS quota and usage through provider dashboard
```

### 5. Firebase Monitoring
- Access Firebase Console → Authentication → Users
- Monitor authentication events in Firebase Console
- Check Firestore usage and queries
- Review Firebase Authentication logs

## Testing Rate Limiting

### 1. Test Authentication Rate Limits
```bash
# Script to test rate limiting
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/auth/initiate" \
    -H "Content-Type: application/json" \
    -d '{"identifier": "test@example.com"}' \
    -w "Request $i: %{http_code}\n"
  sleep 1
done
```

### 2. Test OTP Verification Limits
```bash
# Test OTP attempt limiting
SESSION_ID="your_session_id"
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/v1/auth/verify-otp" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"otp_code\": \"wrong$i\"}" \
    -w "Attempt $i: %{http_code}\n"
done
```

## Troubleshooting Common Issues

### 1. Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Check Redis logs
sudo journalctl -u redis-server -f

# Test Redis connection from Python
python -c "import redis; r=redis.from_url('redis://localhost:6379/0'); print(r.ping())"
```

### 2. SMS Not Received
```bash
# Check SMS provider configuration
curl -X GET "http://app.mydreamstechnology.in/vb/apikey.php" \
  -G -d "apikey=zbAG4xSPKhwqPCI3" \
  -d "senderid=MYDTEH" \
  -d "number=1234567890" \
  -d "message=Test message"

# Verify phone number format (must include country code)
# Correct: +1234567890
# Incorrect: 1234567890
```

### 3. Firebase Authentication Issues
```bash
# Verify Firebase configuration
python -c "
from app.config.firebase import initialize_firebase
try:
    initialize_firebase()
    print('Firebase initialized successfully')
except Exception as e:
    print(f'Firebase error: {e}')
"
```

### 4. Google OAuth Issues
- Verify Google Client ID in environment variables
- Check authorized domains in Google Cloud Console
- Ensure ID token is not expired
- Verify redirect URIs are configured correctly

### 5. Environment Variable Issues
```bash
# Check environment variables
python -c "
from app.config.settings import settings
print(f'Environment: {settings.environment}')
print(f'Redis URL: {settings.redis_url}')
print(f'SMS Provider: {settings.sms_provider}')
print(f'Firebase Project: {settings.firebase_project_id}')
"
```

## Performance Optimization

### 1. Redis Configuration
```bash
# Optimize Redis for authentication workload
# Add to redis.conf:
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 2. Application Tuning
```bash
# Production server configuration
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --worker-connections 1000 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --timeout 30 \
  --keep-alive 5
```

### 3. Database Optimization
- Create indexes on frequently queried fields
- Monitor Firestore usage and optimize queries
- Use connection pooling for high-traffic scenarios

## Security Checklist

### Pre-Production Security Review
- [ ] **Environment Variables**: All secrets properly configured
- [ ] **CORS Origins**: Whitelist configured (no wildcards in production)
- [ ] **Rate Limiting**: Enabled and properly configured
- [ ] **JWT Secrets**: Strong, unique secret keys
- [ ] **SMS Provider**: API keys secured and rate limits understood
- [ ] **Firebase Rules**: Proper security rules configured
- [ ] **HTTPS**: SSL/TLS certificates configured
- [ ] **Logging**: No sensitive data logged
- [ ] **Error Handling**: No sensitive information in error responses

### Security Testing
```bash
# Test CORS configuration
curl -H "Origin: https://malicious-site.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/api/v1/auth/initiate

# Test rate limiting
# (Should return 429 after limit exceeded)

# Test input validation
curl -X POST "http://localhost:8000/api/v1/auth/initiate" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "<script>alert(1)</script>"}'
```

## Deployment Checklist

### Production Deployment Steps
1. **Environment Setup**
   - [ ] Production environment variables configured
   - [ ] Redis server running and accessible
   - [ ] Firebase project configured for production
   - [ ] SMS provider configured with production credentials

2. **Security Configuration**
   - [ ] Strong JWT secret keys
   - [ ] CORS origins properly configured
   - [ ] Rate limiting enabled
   - [ ] HTTPS certificates installed

3. **Monitoring Setup**
   - [ ] Application logging configured
   - [ ] Metrics collection enabled
   - [ ] Health check endpoints accessible
   - [ ] Error alerting configured

4. **Testing**
   - [ ] All authentication flows tested
   - [ ] Rate limiting verified
   - [ ] SMS delivery confirmed
   - [ ] Google OAuth working
   - [ ] Load testing completed

5. **Documentation**
   - [ ] API documentation updated
   - [ ] Deployment procedures documented
   - [ ] Monitoring procedures established
   - [ ] Incident response procedures defined

This comprehensive guide provides everything needed to set up, run, and test the ZODIRA unified authentication system in both development and production environments.