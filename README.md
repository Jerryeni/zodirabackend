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

## 📁 Project Structure

```
zodira_backend/
├── config/
│   ├── __init__.py
│   ├── config.py          # Environment & app configuration
│   └── firebase_config.py # Firebase Admin SDK setup
├── src/
│   ├── __init__.py
│   ├── schemas.py         # Comprehensive Pydantic models
│   ├── i18n.py           # Internationalization support
│   ├── firestore_schema.py # Database schema documentation
│   ├── astrology_engine.py # Vedic astrology calculations
│   ├── auth_utils.py     # Authentication utilities
│   ├── payments.py       # Razorpay payment processing
│   ├── middleware.py     # Custom middleware (metrics, etc.)
│   └── routers/
│       ├── __init__.py
│       ├── auth.py        # Multi-provider authentication
│       ├── users.py       # User & profile management
│       ├── marriage_matching.py # 36 Guna compatibility
│       ├── predictions.py # Astrology predictions
│       ├── astrologers.py # Astrologer management
│       ├── consultations.py # Consultation booking
│       ├── payments.py    # Payment processing
│       └── health.py      # Health checks & metrics
├── firebase-setup.sh     # Automated Firebase setup
├── firestore.rules       # Firestore security rules
├── storage.rules         # Storage security rules
├── FIREBASE_SETUP.md     # Detailed Firebase setup guide
├── Dockerfile           # Container configuration
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── tests/               # Comprehensive test suite
├── docs/                # API documentation
└── README.md
```

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.8+
- Google Cloud SDK (`gcloud`)
- Git

### 2. Clone and Setup
```bash
git clone <repository-url>
cd zodira_backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Firebase Project Setup
Choose one of the following methods:

#### Option A: Automated Setup (Recommended)
```bash
chmod +x firebase-setup.sh
./firebase-setup.sh
```

#### Option B: Manual Setup
Follow the detailed guide in [`FIREBASE_SETUP.md`](FIREBASE_SETUP.md)

### 4. Environment Configuration
Update `.env` file with your Firebase and payment credentials:
```env
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=config/serviceAccountKey.json
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# Razorpay Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

### 5. Deploy Security Rules
Upload `firestore.rules` and `storage.rules` to your Firebase Console:
- **Firestore**: Console → Firestore Database → Rules
- **Storage**: Console → Storage → Rules

## Running the Application

### Development
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### With Uvicorn
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

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

## Testing

Run tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` | Path to Firebase service account JSON | Yes |
| `FIREBASE_PROJECT_ID` | Firebase project ID | Yes |
| `FIREBASE_STORAGE_BUCKET` | Firebase storage bucket | Yes |

## Deployment

### Docker (Planned)
```bash
docker build -t zodira-backend .
docker run -p 8000:8000 zodira-backend
```

### Production Considerations
- Set specific CORS origins instead of `*`
- Use environment-specific configuration
- Implement proper logging and monitoring
- Set up CI/CD pipelines
- Configure Firebase security rules

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

[Add license information]

## Deployment

### Production Setup

1. **Firebase Configuration**:
   - Set up your Firebase project
   - Download the service account key JSON file
   - Upload `firestore.rules` to your Firebase project
   - Enable Authentication and Firestore

2. **Environment Variables**:
   Set the following on your production server:
   ```
   FIREBASE_SERVICE_ACCOUNT_KEY_PATH=/path/to/serviceAccountKey.json
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
   ```

3. **Docker Deployment**:
   ```bash
   docker build -t zodira-backend .
   docker run -d -p 8000:8000 --env-file .env zodira-backend
   ```

4. **Monitoring**:
   - Metrics available at `/metrics` for Prometheus
   - Health check at `/api/v1/health`

Note: Firebase handles database and authentication, so no additional services needed in docker-compose.

## Security

- Rate limiting implemented with slowapi
- Firebase Security Rules enforce data access control
- All endpoints require authentication except health and auth routes

## Support

For questions or issues, please [add contact information]