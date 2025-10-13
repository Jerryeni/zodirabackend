# ZODIRA Backend

A comprehensive FastAPI-based backend for the ZODIRA (Cosmic Predictions) astrology mobile app, providing Vedic astrology calculations, marriage compatibility analysis, personalized predictions, and complete user management.

## 🌟 Features

- **🔐 Advanced Authentication**: Phone, email/password, Google, and Facebook authentication
- **👤 User & Profile Management**: Multi-profile support with detailed birth information
- **💕 Vedic Marriage Matching**: 36 Guna compatibility system with dosha analysis
- **🔮 Personalized Predictions**: Daily, weekly, monthly astrology forecasts
- **👨‍⚕️ Astrologer Management**: Professional astrologer profiles and consultation booking
- **💰 Payment Integration**: Razorpay payment processing for consultations
- **🌐 Multilingual Support**: English and Hindi translations
- **📊 Comprehensive Analytics**: Firebase Analytics integration
- **🔒 Enterprise Security**: Firebase security rules and rate limiting
- **📱 API Documentation**: Complete OpenAPI/Swagger documentation
- **🤖 AI-Powered Predictions**: ChatGPT integration for personalized astrology insights
- **📈 Caching System**: Intelligent caching for astrology calculations and API responses
- **🔄 Persistent Sessions**: Firestore-backed session management for auto-login

## 🛠️ Technology Stack

- **Framework**: FastAPI with async support
- **Database**: Firebase Firestore (NoSQL)
- **Authentication**: Firebase Auth (Phone, Email, OAuth)
- **Storage**: Firebase Cloud Storage
- **Payments**: Razorpay integration
- **Validation**: Pydantic v2 with comprehensive schemas
- **Internationalization**: Custom i18n system (English/Hindi)
- **Rate Limiting**: SlowAPI middleware
- **Monitoring**: Prometheus metrics
- **Testing**: pytest with async support
- **Containerization**: Docker ready
- **Deployment**: Google Cloud Run
- **AI**: OpenAI ChatGPT API for predictions
- **Caching**: File-based caching for astrology calculations

## 📁 Project Structure

```
zodira_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── unified_auth.py      # Authentication endpoints
│   │       ├── user_management.py   # User & profile management
│   │       ├── astrology.py         # Astrology chart generation
│   │       ├── enhanced_astrology.py # Enhanced features & predictions
│   │       └── health.py            # Health checks
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py        # Environment & app configuration
│   │   └── firebase.py        # Firebase Admin SDK setup
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py        # JWT, password hashing, validation
│   │   ├── dependencies.py    # FastAPI dependencies
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── middleware.py      # Custom middleware
│   │   └── security.py        # Security utilities
│   ├── models/
│   │   ├── __init__.py
│   │   ├── astrology.py       # Astrology data models
│   │   ├── profile.py         # User profile models
│   │   └── user.py            # User models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication schemas
│   │   └── astrology.py       # Astrology schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py           # User management & auth
│   │   ├── astrology_service.py      # Astrology calculations
│   │   ├── enhanced_astrology_service.py # Enhanced features
│   │   ├── auth_service.py           # Authentication service
│   │   ├── firebase_email_service.py # Email service
│   │   ├── chatgpt_service.py        # AI predictions
│   │   └── user_service.py           # User management
│   └── utils/
│       ├── __init__.py
│       ├── astrology_utils.py  # Astrology utilities
│       └── firebase_utils.py   # Firebase utilities
├── cache/
│   └── astrology/             # Cached astrology calculations
├── tests/
│   ├── __init__.py
│   ├── test_health.py         # Health endpoint tests
│   └── test_unified_auth.py   # Authentication tests
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Container configuration
├── requirements.txt           # Python dependencies
├── firebase.json              # Firebase configuration
├── firestore.rules            # Firestore security rules
├── storage.rules              # Storage security rules
├── .env.example               # Environment variables template
├── .env                       # Environment variables (gitignored)
├── .gitignore                 # Git ignore rules
├── app.log                    # Application logs
└── README.md                  # This file
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11+ (recommended)
- Google Cloud SDK (`gcloud`) - for Firebase deployment
- Git
- Docker (optional, for containerized deployment)

### Quick Start (Local Development)

1. **Clone the repository**
```bash
git clone <repository-url>
cd zodira_backend
```

2. **Set up Python environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
# Copy template
cp .env.example .env

# Edit .env with your configuration (see Environment Variables section below)
```

4. **Run the application**
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# OR using the main.py script
python app/main.py
```

5. **Verify installation**
```bash
# Check health endpoint
curl http://localhost:8000/api/v1/health

# View API documentation
open http://localhost:8000/docs
```

### Firebase Setup

#### Automated Setup (Recommended)
```bash
# Make setup script executable and run
chmod +x firebase-setup.sh
./firebase-setup.sh
```

#### Manual Setup
1. Create a Firebase project at https://console.firebase.google.com/
2. Enable Authentication with Email/Password, Phone, and Google providers
3. Enable Firestore Database
4. Enable Cloud Storage
5. Generate a service account key and download the JSON file
6. Deploy security rules:
   - Upload `firestore.rules` to Firestore → Rules
   - Upload `storage.rules` to Storage → Rules

### Docker Deployment

#### Local Docker Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# OR build and run manually
docker build -t zodira-backend .
docker run -p 8000:8000 --env-file .env zodira-backend
```

#### Production Deployment
```bash
# Build for production
docker build -t zodira-backend:prod -f Dockerfile.prod .

# Run in production mode
docker run -d -p 8000:8000 --env-file .env.prod zodira-backend:prod
```

### Environment Configuration

The application uses the following environment variables (see `.env.example` for template):

#### Required Variables
```env
# Application
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key-here

# Firebase (Required)
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CLIENT_EMAIL=firebase-service-account@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

#### Optional Variables
```env
# Authentication
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
REDIRECT_URI=https://your-domain.com/auth/google/callback

# SMS/Email Services
MYDREAMS_API_KEY=your-sms-api-key
FIREBASE_EMAIL_USER=your-email@gmail.com
FIREBASE_EMAIL_PASSWORD=your-app-password

# AI Features
OPENAI_API_KEY=your-openai-api-key

# Payment Processing
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret

# Rate Limiting & Security
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### Architecture Notes

- **Session Management**: Uses Firestore for persistent sessions (no Redis required)
- **Rate Limiting**: Firestore-based fixed-window rate limiting
- **Caching**: File-based caching for astrology calculations in `cache/astrology/`
- **Authentication**: JWT tokens with Firebase Auth integration
- **Database**: Firebase Firestore with security rules
- **Storage**: Firebase Cloud Storage for user files
## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

### 📡 Key API Endpoints

#### 🔍 Health & Monitoring
- `GET /api/v1/health` - Service and database health check
- `GET /metrics` - Prometheus metrics

#### 🔐 Authentication
- `POST /api/v1/auth/register` - Email/password registration
- `POST /api/v1/auth/login` - Email/password login
- `POST /api/v1/auth/phone/send-verification` - Send phone OTP
- `POST /api/v1/auth/phone/verify` - Verify phone OTP
- `POST /api/v1/auth/oauth/login` - OAuth login (Google/Facebook)
- `POST /api/v1/auth/verify-token` - Token verification

#### 👤 User Management
- `POST /api/v1/users/{user_id}` - Create user profile
- `GET /api/v1/users/{user_id}` - Get user details
- `GET /api/v1/users/profiles` - List user profiles
- `POST /api/v1/users/profiles` - Create person profile
- `GET /api/v1/users/profiles/{profile_id}` - Get profile details
- `PUT /api/v1/users/profiles/{profile_id}` - Update profile
- `DELETE /api/v1/users/profiles/{profile_id}` - Delete profile

#### 💕 Marriage Compatibility
- `POST /api/v1/marriage-matching` - Calculate compatibility match
- `GET /api/v1/marriage-matching` - List user's matches
- `GET /api/v1/marriage-matching/{match_id}` - Get match details
- `DELETE /api/v1/marriage-matching/{match_id}` - Delete match

#### 🔮 Astrology Predictions
- `POST /api/v1/predictions/daily` - Generate daily prediction
- `POST /api/v1/predictions/weekly` - Generate weekly prediction
- `POST /api/v1/predictions/monthly` - Generate monthly prediction
- `GET /api/v1/predictions/history/{profile_id}` - Prediction history

#### 👨‍⚕️ Astrologer Management
- `GET /api/v1/astrologers` - List astrologers (with filtering)
- `GET /api/v1/astrologers/{astrologer_id}` - Get astrologer details
- `GET /api/v1/astrologers/availability/{astrologer_id}` - Check availability
- `POST /api/v1/astrologers/{astrologer_id}/reviews` - Add review

#### 📅 Consultations
- `POST /api/v1/consultations/book` - Book consultation
- `GET /api/v1/consultations` - List user's consultations
- `GET /api/v1/consultations/{consultation_id}` - Get consultation details
- `PUT /api/v1/consultations/{consultation_id}/cancel` - Cancel consultation
- `PUT /api/v1/consultations/{consultation_id}/complete` - Mark as completed
- `POST /api/v1/consultations/{consultation_id}/review` - Add consultation review

#### 💰 Payments
- `POST /api/v1/payments/create-order` - Create payment order
- `POST /api/v1/payments/verify` - Verify payment completion
- `GET /api/v1/payments/history` - Payment history
- `POST /api/v1/payments/refund/{payment_id}` - Request refund

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run tests with verbose output
pytest -v
```

### Test Structure
- **Unit Tests**: Test individual functions and services
- **Integration Tests**: Test API endpoints and database interactions
- **Authentication Tests**: Verify auth flows and security
- **Astrology Tests**: Test astrology calculations and caching

### Writing Tests
```python
# Example test structure
import pytest
from app.services.user_service import user_service

def test_user_creation():
    # Test user creation logic
    pass

def test_astrology_calculation():
    # Test astrology calculation accuracy
    pass
```

## 🔧 Environment Variables

### Complete Configuration Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Application environment | No | `development` |
| `SECRET_KEY` | JWT signing key (32+ chars) | Yes | - |
| `APP_DEBUG` | Enable debug mode | No | `false` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration time | No | `43200` |

### Firebase Configuration
| Variable | Description | Required |
|----------|-------------|----------|
| `FIREBASE_PROJECT_ID` | Firebase project ID | Yes |
| `FIREBASE_CLIENT_EMAIL` | Service account email | Yes |
| `FIREBASE_PRIVATE_KEY_ID` | Private key ID | Yes |
| `FIREBASE_PRIVATE_KEY` | Private key (with \n literals) | Yes |
| `FIREBASE_STORAGE_BUCKET` | Cloud Storage bucket | Yes |

### Authentication & OAuth
| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | No |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | No |
| `REDIRECT_URI` | OAuth redirect URI | No |

### External Services
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for predictions | No |
| `MYDREAMS_API_KEY` | SMS service API key | No |
| `RAZORPAY_KEY_ID` | Payment gateway key | No |
| `RAZORPAY_KEY_SECRET` | Payment gateway secret | No |

### Security & Performance
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ALLOWED_ORIGINS` | CORS allowed origins | No | `*` |
| `RATE_LIMIT_REQUESTS` | Requests per window | No | `100` |
| `RATE_LIMIT_WINDOW` | Rate limit window (seconds) | No | `60` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

## 🚀 Deployment

### Production Deployment Options

#### 1. Google Cloud Run (Recommended)
```bash
# Build and deploy to Cloud Run
gcloud run deploy zodira-backend \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production" \
  --memory=1Gi \
  --cpu=1
```

#### 2. Docker Container
```bash
# Build production image
docker build -t zodira-backend:prod .

# Run with production environment
docker run -d \
  --name zodira-backend \
  -p 8000:8000 \
  --env-file .env.prod \
  --restart unless-stopped \
  zodira-backend:prod
```

#### 3. Kubernetes Deployment
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zodira-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zodira-backend
    template:
      metadata:
        labels:
          app: zodira-backend
      spec:
        containers:
        - name: zodira-backend
          image: zodira-backend:prod
          ports:
          - containerPort: 8000
          envFrom:
          - configMapRef:
              name: zodira-config
          - secretRef:
              name: zodira-secrets
```

### Production Considerations

#### Security
- **Environment Variables**: Never commit secrets to version control
- **CORS**: Set specific origins instead of `*` in production
- **HTTPS**: Always use HTTPS in production
- **Secrets Management**: Use Google Cloud Secret Manager or similar

#### Performance
- **Caching**: Astrology calculations are cached for performance
- **Rate Limiting**: Configurable rate limits prevent abuse
- **Database**: Firestore scales automatically
- **Monitoring**: Prometheus metrics available at `/metrics`

#### Monitoring & Observability
```bash
# Health checks
curl https://your-domain.com/api/v1/health

# Metrics endpoint
curl https://your-domain.com/metrics

# Application logs
docker logs zodira-backend
```

## 🔒 Security

### Authentication & Authorization
- **JWT Tokens**: Short-lived access tokens with secure signing
- **Firebase Auth**: Integration with Google, email, and phone authentication
- **Session Management**: Firestore-backed persistent sessions
- **Rate Limiting**: Fixed-window rate limiting on authentication endpoints

### Data Protection
- **Encryption**: All data encrypted in transit and at rest
- **Input Validation**: Comprehensive Pydantic validation
- **SQL Injection Prevention**: No SQL queries (Firestore)
- **XSS Protection**: Input sanitization and validation

### Firebase Security Rules
```javascript
// firestore.rules - Key security rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Profiles are user-specific
    match /person_profiles/{profileId} {
      allow read, write: if request.auth != null &&
        resource.data.user_id == request.auth.uid;
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Firebase Connection Issues
```bash
# Check Firebase configuration
curl http://localhost:8000/api/v1/health

# Verify environment variables
echo $FIREBASE_PROJECT_ID
echo $FIREBASE_CLIENT_EMAIL
```

#### 2. Astrology API Failures
```bash
# Check cache directory permissions
ls -la cache/astrology/

# Verify API key configuration
echo $FREE_ASTRO_API_KEY
```

#### 3. Authentication Problems
```bash
# Test authentication endpoint
curl -X POST http://localhost:8000/api/v1/auth/health

# Check JWT token validity
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/health
```

#### 4. Docker Issues
```bash
# Check container logs
docker logs zodira-backend

# Verify environment file
docker exec zodira-backend env | grep FIREBASE
```

### Debug Mode
Enable debug logging:
```env
APP_DEBUG=true
LOG_LEVEL=DEBUG
```

### Performance Issues
- Check cache hit rates in application logs
- Monitor Firestore usage in Firebase Console
- Review rate limiting configurations

## 🤝 Contributing

### Development Workflow
1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes with tests**
4. **Run tests and linting**
   ```bash
   pytest
   black app/
   flake8 app/
   ```
5. **Submit a pull request**

### Code Standards
- **Python**: Follow PEP 8 style guidelines
- **Documentation**: Add docstrings to all functions
- **Testing**: Write tests for new features
- **Commits**: Use conventional commit messages

### Branch Naming
- `feature/feature-name`: New features
- `bugfix/bug-description`: Bug fixes
- `hotfix/critical-fix`: Critical fixes
- `docs/documentation`: Documentation updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

### Contact Information
- **Email**: support@zodira.app
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation**: [API Docs](http://localhost:8000/docs)

### Community
- **Discord**: Join our community server
- **Forum**: Community discussion forum
- **Newsletter**: Subscribe for updates

---

**Built with ❤️ for the ZODIRA astrology community**
# Backend API Specification and Implementation Guide

Audience: Flutter developers integrating the ZODIRA backend  
Base URL (local): http://localhost:8000
Production API Base URL: https://zodirabackend-506518268983.asia-east1.run.app
API Version: v1  
Auth: Bearer JWT from /api/v1/auth, persistent session supported  
Data store: Firestore  
Sessions and rate limiting: Firestore-based (no Redis)

References to code:
- App wiring [FastAPI()](app/main.py:35), routers include health, auth, users, astrology, enhanced.
- Auth router [router](app/api/v1/unified_auth.py) exposes initiate, verify-otp, google-oauth, google login and callback, logout, health.
- Unified auth service [UserService](app/services/user_service.py:57) implements OTP flows, Google OAuth, persistent sessions.
- JWT creation [create_access_token()](app/core/security.py:65), verification [verify_token()](app/core/security.py:92).
- Auth dependency [get_current_user()](app/core/dependencies.py:10).
- Health endpoint [health_check()](app/api/v1/health.py:11).
- Enhanced astrology endpoints [router](app/api/v1/enhanced_astrology.py).
- Astrology classic endpoints [router](app/api/v1/astrology.py).

## 1. Authentication Overview

Auth mechanisms supported:
- Email or Phone OTP login initiated via /api/v1/auth/initiate and completed via /api/v1/auth/verify-otp.
- Google OAuth:
  - GET /api/v1/auth/google/login returns the Google consent URL
  - The OAuth redirect URI must be set to /api/v1/auth/google/callback
- Persistent session for auto-login across app starts is supported via enhanced endpoints:
  - POST /api/v1/enhanced/auth/persistent-login
  - POST /api/v1/enhanced/auth/logout and GET /api/v1/enhanced/auth/sessions

JWTs are short-lived access tokens created by [create_access_token()](app/core/security.py:65) and verified by [verify_token()](app/core/security.py:92). The current design does not include refresh tokens; instead, a Firestore-backed persistent session is used for auto-login.

Required request header for protected endpoints:
- Authorization: Bearer {access_token}

### 1.1 Rate limiting
- Firestore fixed-window rate limiting is applied to OTP initiation [UserService._check_rate_limit()](app/services/user_service.py:142)
- Global SlowAPI middleware is enabled in [app.main](app/main.py:44). Per-route decorators are not currently configured.

### 1.2 Error format
- Error responses are standard FastAPI HTTPException JSON: { "detail": "message" }
- Common status codes: 400 validation, 401 unauthorized, 403 forbidden, 404 not found, 500 server error

## 2. Authentication API

Router: /api/v1/auth from [router](app/api/v1/unified_auth.py)

### 2.1 Initiate OTP
POST /api/v1/auth/initiate  
Body:
{
  "identifier": "user@example.com"
}

- identifier can be email or E.164 phone number.
- On success, creates Firestore auth session and attempts delivery via email or SMS.

Response 200:
{
  "session_id": "string",
  "auth_type": "email or phone",
  "status": "otp_sent",
  "message": "OTP sent to your email address",
  "expires_in": 300,
  "next_step": "verify_otp"
}

Implementation [initiate_authentication()](app/api/v1/unified_auth.py:112) -> [UserService.initiate_auth()](app/services/user_service.py:83)

Notes:
- SMS integration uses MyDreams API. Email uses SMTP credentials. Delivery can be disabled in dev while sessions still persist.

### 2.2 Verify OTP
POST /api/v1/auth/verify-otp  
Body:
{
  "session_id": "string",
  "otp_code": "123456"
}

Response 200:
{
  "session_id": "string",
  "access_token": "jwt",
  "user_id": "uid",
  "status": "authenticated",
  "is_new_user": false,
  "next_step": "dashboard or complete_profile",
  "user_data": {
    "uid": "uid",
    "email": "user@example.com",
    "phone": null,
    "display_name": null,
    "profile_complete": false
  }
}

Implementation [verify_otp()](app/api/v1/unified_auth.py:130) -> [UserService.verify_otp()](app/services/user_service.py:344)

Server behavior:
- Validates session and OTP, creates user in Firebase Auth if needed, ensures a Firestore 'users' document exists, generates JWT [create_access_token()](app/core/security.py:65), creates a persistent session token [create_persistent_session()](app/services/user_service.py:769), and computes next_step based on profiles [UserService._determine_next_step()](app/services/user_service.py:525)

### 2.3 Google OAuth
GET /api/v1/auth/google/login  
- Returns a JSON with a URL for Google consent.

Response 200:
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?...state..."
}

Implementation [google_login()](app/api/v1/unified_auth.py:158)

GET /api/v1/auth/google/callback?code=...&state=...
- Exchanges code for tokens and fetches userinfo; logs the user in, creates Firestore profile data if needed.

Response 200:
{
  "access_token": "jwt",
  "user": { ...user_data... },
  "is_new_user": false,
  "next_step": "dashboard"
}

Implementation [google_callback()](app/api/v1/unified_auth.py:171) -> [UserService.handle_google_user()](app/services/user_service.py:622)

### 2.4 Logout
POST /api/v1/auth/logout  
Headers:
- Authorization: Bearer {access_token}

Body:
{
  "session_id": "optional-current-session-id"
}

Response 200:
{
  "message": "Logged out successfully"
}

Implementation [logout()](app/api/v1/unified_auth.py:211) -> [UserService.logout()](app/services/user_service.py:706)

Note:
- If using persistent sessions, use /api/v1/enhanced/auth/logout with session_token to invalidate that session (see section 4).

### 2.5 Auth health
GET /api/v1/auth/health  
Response 200:
{
  "status": "healthy",
  "firebase": "connected"
}

Implementation [auth_health_check()](app/api/v1/unified_auth.py:222)

## 3. User and Profile APIs

Router: /api/v1/users from [router](app/api/v1/user_management.py)

Headers for all endpoints: Authorization: Bearer {access_token}

### 3.1 Get profiles
GET /api/v1/users/profiles  
Response 200:
[
  {
    "id": "profile_id",
    "userId": "uid",
    "name": "John Doe",
    "birth_date": "1990-01-01",
    "birth_time": "08:59:00",
    "birth_place": "City, Country",
    "gender": "male",
    "zodiac_sign": "Aries",
    "nakshatra": "Rohini",
    "moon_sign": "Taurus",
    "createdAt": "timestamp",
    "updated_at": "timestamp"
  }
]

Implementation [get_profiles()](app/api/v1/user_management.py:504)

### 3.2 Create profile
POST /api/v1/users/profiles  
Body:
{
  "user_id": "optional, server uses token if provided mismatch",
  "name": "John Doe",
  "birthDate": "1990-01-01",
  "birthTime": "08:59:00",
  "birthPlace": "City, Country",
  "gender": "male",
  "created_at": "2024-01-01T12:00:00Z"
}

Response 200: ProfileResponse (same fields as GET)  
Implementation [create_profile()](app/api/v1/user_management.py:631)

Notes:
- The server uses the authenticated userId from the token. If user_id in body mismatches token, token wins.

### 3.3 Get profile
GET /api/v1/users/profiles/{profile_id}  
Response 200: ProfileResponse  
Implementation [get_profile_or_status()](app/api/v1/user_management.py:735)

### 3.4 Update profile
PUT /api/v1/users/profiles/{profile_id}  
Body: PersonProfile model fields  
Response 200: ProfileResponse  
Implementation [update_profile()](app/api/v1/user_management.py:784)

### 3.5 Delete profile
DELETE /api/v1/users/profiles/{profile_id}  
Response 200:
{
  "message": "Profile deleted successfully"
}

Implementation [delete_profile()](app/api/v1/user_management.py:836)

### 3.6 User details and dashboard
- GET /api/v1/users/user-details returns a comprehensive user payload with profiles and predictions [get_user_details()](app/api/v1/user_management.py:274)
- GET /api/v1/users/dashboard returns summary data for dashboards [get_user_dashboard()](app/api/v1/user_management.py:521)

## 4. Enhanced Astrology and Persistent Auth APIs

Router: /api/v1/enhanced from [router](app/api/v1/enhanced_astrology.py)

Headers: Authorization: Bearer {access_token}

### 4.1 Persistent authentication
- POST /api/v1/enhanced/auth/persistent-login
  - Header: Authorization: Bearer {persistent_session_token}
  - Returns new access_token and next_step
  - Implementation [persistent_login()](app/api/v1/enhanced_astrology.py:33) -> [UserService.check_persistent_login()](app/services/user_service.py:1021)

- POST /api/v1/enhanced/auth/logout?session_token=...
  - Invalidates the persistent session for the current user
  - Implementation [logout()](app/api/v1/enhanced_astrology.py:68) -> [UserService.invalidate_persistent_session()](app/services/user_service.py:917)

- GET /api/v1/enhanced/auth/sessions
  - Lists active sessions for the current user
  - Implementation [get_user_sessions()](app/api/v1/enhanced_astrology.py:91) -> [UserService.get_user_sessions()](app/services/user_service.py:984)

### 4.2 Enhanced profile and predictions
- POST /api/v1/enhanced/profiles/{profile_id}/generate-chart
  - Generates chart and predictions for a profile
  - Implementation [generate_profile_chart()](app/api/v1/enhanced_astrology.py:128)

- GET /api/v1/enhanced/profiles/{profile_id}/complete
  - Full profile with chart, predictions, matches
  - Implementation [get_complete_profile()](app/api/v1/enhanced_astrology.py:175)

- GET /api/v1/enhanced/profiles/{profile_id}/predictions?prediction_type=daily|weekly|monthly|yearly|career|health|relationship|finance
  - Filterable predictions
  - Implementation [get_profile_predictions()](app/api/v1/enhanced_astrology.py:204)

- POST /api/v1/enhanced/profiles/{profile_id}/predictions/{prediction_type}
  - Generates a specific prediction on demand
  - Implementation [generate_specific_prediction()](app/api/v1/enhanced_astrology.py:245)

- POST /api/v1/enhanced/profiles/{profile_id}/refresh-predictions
  - Batch regenerate predictions
  - Implementation [refresh_profile_predictions()](app/api/v1/enhanced_astrology.py:526)

### 4.3 Marriage matching
- POST /api/v1/enhanced/marriage-matching/generate
  - Body includes partner_data with name, birth_date, birth_time, birth_place, gender
  - Implementation [generate_marriage_match()](app/api/v1/enhanced_astrology.py:316)

- GET /api/v1/enhanced/marriage-matching/{match_id}
  - Returns match and partner profile
  - Implementation [get_marriage_match()](app/api/v1/enhanced_astrology.py:366)

- GET /api/v1/enhanced/profiles/{profile_id}/marriage-matches
  - Lists matches for a profile
  - Implementation [get_profile_marriage_matches()](app/api/v1/enhanced_astrology.py:417)

### 4.4 Dashboard
- GET /api/v1/enhanced/dashboard
  - Consolidated view of profiles, predictions, matches
  - Implementation [get_dashboard_data()](app/api/v1/enhanced_astrology.py:451)

## 5. Astrology APIs (Classic)

Router: /api/v1/astrology from [router](app/api/v1/astrology.py)

- POST /api/v1/astrology/generate-chart
  - Body: { "profile_id": "uuid" }
  - Starts background chart generation if not already present
  - Implementation [generate_astrology_chart()](app/api/v1/astrology.py:106)

- GET /api/v1/astrology/chart/{profile_id}
  - Returns AstrologyChartResponse if available
  - Implementation [get_astrology_chart()](app/api/v1/astrology.py:180)

- GET /api/v1/astrology/chart/{profile_id}/status
  - completed or not_found
  - Implementation [get_chart_generation_status()](app/api/v1/astrology.py:236)

- DELETE /api/v1/astrology/chart/{profile_id}
  - Deletes the stored chart
  - Implementation [delete_astrology_chart()](app/api/v1/astrology.py:281)

## 6. Health and Observability

- GET /api/v1/health
  - Database ping and app version
  - Implementation [health_check()](app/api/v1/health.py:11)

- GET /metrics
  - Prometheus text metrics
  - Implementation [metrics handler](app/main.py:83)

## 7. JWT and Security

JWT Claims:
- sub: user id
- email or phone depending on auth
- auth_type: email, phone, google, or persistent_session
- iat, exp, jti, iss

Create and verify:
- [create_access_token()](app/core/security.py:65)
- [verify_token()](app/core/security.py:92)

Auth dependency:
- [get_current_user()](app/core/dependencies.py:10) extracts user_id from JWT sub and raises 401 on invalid token.

Logout semantics:
- API token invalidation is logical; consider using token blacklist [blacklist_token()](app/core/security.py:126) for hard logout flows if needed.

## 8. Firestore Collections

Key collections with typical documents:

- users
  - id: user_id
  - fields: email, phone, displayName, createdAt, lastLoginAt, profile_complete, subscriptionType, google_id optional
- person_profiles
  - id: profile_id
  - fields: user_id, name, birth_date, birth_time, birth_place, gender, astrology fields, created_at, updated_at, is_active
- auth_sessions (ephemeral)
  - id: session_id
  - fields: identifier, auth_type, otp_code, expires_at ISO, attempts, max_attempts, status
- rate_limits
  - id: auth_rate_limit:hash
  - fields: attempts, window_started_at
- user_sessions (persistent login)
  - id: session_token
  - fields: user_id, created_at, last_accessed, expires_at, is_active, device_info
- predictions
  - id: profileId_type_timestamp
  - fields: profile_id, user_id, prediction_type, prediction_text, created_at, expires_at, is_active
- marriage_matches
  - id: uuid
  - fields: user_id, main_profile_id, partner_profile_id, overall_score, guna_score, strengths, challenges, created_at, is_active
- astrology_charts
  - id: userId_profileId
  - fields: houses, vimshottari_dasha, birth_details, created_at, updated_at

## 9. Request Examples

Headers for protected endpoints:
Authorization: Bearer {access_token}

Auth initiate
curl -X POST http://localhost:8000/api/v1/auth/initiate \
  -H "Content-Type: application/json" \
  -d '{"identifier":"user@example.com"}'

Verify OTP
curl -X POST http://localhost:8000/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION","otp_code":"123456"}'

Google login URL
curl http://localhost:8000/api/v1/auth/google/login

Create profile
curl -X POST http://localhost:8000/api/v1/users/profiles \
  -H "Authorization: Bearer ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","birthDate":"1990-01-01","birthTime":"08:59:00","birthPlace":"City, Country","gender":"male","created_at":"2024-01-01T12:00:00Z"}'

Get complete profile
curl http://localhost:8000/api/v1/enhanced/profiles/PROFILE_ID/complete \
  -H "Authorization: Bearer ACCESS"

Generate daily prediction
curl -X POST http://localhost:8000/api/v1/enhanced/profiles/PROFILE_ID/predictions/daily \
  -H "Authorization: Bearer ACCESS"

### Error responses
- 401 Unauthorized:
  {
    "detail": "Invalid or expired token"
  }
- 403 Forbidden:
  {
    "detail": "Access denied"
  }
- 404 Not Found:
  {
    "detail": "Profile not found"
  }

## 10. Flutter Integration Notes

Headers and tokens:
- Store the access_token securely (Flutter secure storage).
- For auto-login, store the persistent_session_token returned by verify-otp response in the field persistent_session_token if used; then call POST /api/v1/enhanced/auth/persistent-login with Authorization: Bearer {persistent_session_token} on app start to retrieve a fresh access_token and next_step.

Next step handling:
- Next step can be complete_profile or dashboard. Route users accordingly:
  - complete_profile: navigate to profile creation view
  - dashboard: show main app dashboard using /api/v1/enhanced/dashboard

Phone numbers:
- Use E.164 format for identifiers when initiating phone OTP.
- The backend normalizes some formats for Indian numbers; always prefer E.164.

Timeouts and retries:
- For OTP delivery, the API returns 200 even when SMTP or SMS provider fails, relying on logs; the client should show a standard message and allow resending by calling /api/v1/auth/initiate again.

Pagination:
- List endpoints currently return limited documents without pagination metadata. If datasets grow large, pagination parameters will be added.

CORS and environments:
- In production, set ALLOWED_ORIGINS to your Flutter app web origin if using web builds. See [settings](app/config/settings.py:25).

## 11. Sequence Diagrams

OTP Login (Email or Phone)
```mermaid
sequenceDiagram
participant Client
participant API
participant Firestore
Client->>API: POST /api/v1/auth/initiate identifier
API->>Firestore: Create auth_sessions and rate_limits
API-->>Client: session_id otp_sent
Client->>API: POST /api/v1/auth/verify-otp session_id otp_code
API->>Firestore: Validate session create user profile
API-->>Client: access_token next_step persistent_session_token
```

Google OAuth Flow
```mermaid
sequenceDiagram
participant Client
participant API
participant Google
participant Firestore
Client->>API: GET /api/v1/auth/google/login
API-->>Client: url to Google consent
Client->>Google: Open consent url
Google-->>Client: Redirect with code
Client->>API: GET /api/v1/auth/google/callback code state
API->>Google: Exchange code for tokens get userinfo
API->>Firestore: Upsert user document
API-->>Client: access_token user_data next_step
```

## 12. Non-Docker Local Development

Follow the steps in the Local development section of this README. Key points:
- Ensure Firebase env vars are set; private key uses literal \\n which the code converts in [initialize_firebase()](app/config/firebase.py:16)
- Run with:
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## 13. Production Notes

- Restrict CORS in [settings](app/config/settings.py:25)
- Rotate and secure secrets
- Consider Firestore TTL for auth_sessions and user_sessions
- Add per-route SlowAPI decorators if you want stricter API wide limits

## 14. Backward Compatibility and Deprecations

- Old auth endpoints under /api/v1/users such as initiate and verify-otp are deprecated and return HTTP 410 Gone in [user_management router](app/api/v1/user_management.py:215)
- Use the unified auth endpoints under /api/v1/auth instead.
