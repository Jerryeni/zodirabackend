# 🚀 ZODIRA Backend API - Complete Frontend Integration Guide

## 📋 Overview

This comprehensive guide provides everything needed to integrate a frontend application with the ZODIRA astrology platform backend. The backend is built with FastAPI, Firebase Authentication, and provides complete astrology services including predictions, marriage matching, consultations, and payments.

## 🏗️ Backend Architecture

**Base URL:** `http://localhost:8000` (Development) | `https://api.zodira.app` (Production)

**Tech Stack:**
- **Framework:** FastAPI with async/await
- **Authentication:** Firebase Auth + Custom JWT
- **Database:** Google Firestore
- **Payment:** Razorpay Integration
- **SMS:** MyDreams Technology API
- **Email:** SMTP (Gmail/Outlook/Custom)

## 🔐 Authentication System

### 1. Unified Authentication (Email/Phone/Google OAuth)

**Base Route:** `/api/v1/auth`

#### 1.1 Initiate Authentication
```http
POST /api/v1/auth/initiate
Content-Type: application/json

{
  "identifier": "user@example.com" | "+919876543210"
}
```

**Response:**
```json
{
  "session_id": "abc123...",
  "auth_type": "email" | "phone",
  "status": "otp_sent",
  "message": "OTP sent to your email/phone",
  "expires_in": 300,
  "next_step": "verify_otp",
  "debug_otp": "123456",
  "identifier": "user@example.com",
  "delivery_method": "email" | "sms"
}
```

#### 1.2 Verify OTP
```http
POST /api/v1/auth/verify-otp
Content-Type: application/json

{
  "session_id": "abc123...",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "session_id": "abc123...",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": "firebase_uid",
  "status": "authenticated",
  "is_new_user": false,
  "next_step": "dashboard" | "complete_profile",
  "user_data": {
    "uid": "firebase_uid",
    "email": "user@example.com",
    "phone": "+919876543210",
    "display_name": "User Name",
    "profile_complete": true
  }
}
```

#### 1.3 Google OAuth Login
```http
POST /api/v1/auth/google-oauth
Content-Type: application/json

{
  "id_token": "google_id_token_from_frontend"
}
```

#### 1.4 Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}

{
  "session_id": "abc123..."
}
```

#### 1.5 Session Status Check
```http
GET /api/v1/auth/session-status?session_id=abc123
Authorization: Bearer {access_token}
```

#### 1.6 Resend OTP
```http
POST /api/v1/auth/resend-otp
Content-Type: application/json

{
  "session_id": "abc123..."
}
```

## 👤 User Profile Management

**Base Route:** `/api/v1/profiles`

#### 2.1 Create User Profile
```http
POST /api/v1/profiles/{user_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "id": "user_id",
  "email": "user@example.com",
  "phone": "+919876543210",
  "display_name": "User Name",
  "subscription_type": "free",
  "language": "en",
  "timezone": "Asia/Kolkata"
}
```

#### 2.2 Get User Profile
```http
GET /api/v1/profiles/{user_id}
Authorization: Bearer {access_token}
```

#### 2.3 Get All Person Profiles
```http
GET /api/v1/profiles/profiles
Authorization: Bearer {access_token}
```

#### 2.4 Create Person Profile (for astrology)
```http
POST /api/v1/profiles/profiles
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "John Doe",
  "birth_date": "1990-05-15",
  "birth_time": "14:30:00",
  "birth_place": "Mumbai, India",
  "latitude": 19.0760,
  "longitude": 72.8777,
  "timezone": "Asia/Kolkata",
  "gender": "male",
  "profile_type": "self"
}
```

**Response:**
```json
{
  "id": "profile_id",
  "userId": "user_id",
  "name": "John Doe",
  "birthDate": "1990-05-15",
  "birthTime": "14:30:00",
  "birthPlace": "Mumbai, India",
  "gender": "male",
  "zodiacSign": "Taurus",
  "nakshatra": "Rohini",
  "rashi": "Vrishabha"
}
```

#### 2.5 Update Person Profile
```http
PUT /api/v1/profiles/profiles/{profile_id}
Authorization: Bearer {access_token}
```

#### 2.6 Delete Person Profile
```http
DELETE /api/v1/profiles/profiles/{profile_id}
Authorization: Bearer {access_token}
```

## 🔮 Astrology Predictions

**Base Route:** `/api/v1/predictions`

#### 3.1 Generate Daily Prediction
```http
POST /api/v1/predictions/daily
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "profile_id": "profile_id",
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "prediction_id": "pred_123",
  "user_id": "user_id",
  "profile_id": "profile_id",
  "prediction_type": "daily",
  "date": "2024-01-15",
  "title": "Daily Horoscope for John Doe",
  "overall_prediction": "Today brings positive energy...",
  "career": "Focus on important meetings...",
  "love_relationships": "Communication is key...",
  "health": "Take care of your diet...",
  "finance": "Avoid major investments...",
  "lucky_numbers": [7, 14, 21],
  "lucky_colors": ["blue", "green"],
  "lucky_directions": ["north", "east"],
  "favorable_time": "10:00 AM - 2:00 PM",
  "avoid_time": "6:00 PM - 8:00 PM",
  "generated_at": "2024-01-15T06:00:00Z",
  "expires_at": "2024-01-16T06:00:00Z"
}
```

#### 3.2 Generate Weekly Prediction
```http
POST /api/v1/predictions/weekly
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "profile_id": "profile_id",
  "date": "2024-01-15"
}
```

#### 3.3 Generate Monthly Prediction
```http
POST /api/v1/predictions/monthly
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "profile_id": "profile_id",
  "date": "2024-01-15"
}
```

#### 3.4 Get Prediction History
```http
GET /api/v1/predictions/history/{profile_id}?limit=10&offset=0
Authorization: Bearer {access_token}
```

## 💑 Marriage Matching

**Base Route:** `/api/v1/marriage-matching`

#### 4.1 Create Marriage Match
```http
POST /api/v1/marriage-matching/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "male_profile_id": "male_profile_id",
  "female_profile_id": "female_profile_id",
  "matching_type": "detailed",
  "language": "en"
}
```

**Response:**
```json
{
  "id": "match_id",
  "male_profile_id": "male_profile_id",
  "female_profile_id": "female_profile_id",
  "total_gunas": 24,
  "compatibility_percentage": 66.67,
  "overall_match": "Good Match",
  "guna_breakdown": {
    "varna": 1,
    "vasya": 2,
    "tara": 3,
    "yoni": 4,
    "graha_maitri": 5,
    "gana": 6,
    "bhakoot": 0,
    "nadi": 3
  },
  "dosha_analysis": {
    "manglik_dosha": {
      "male_manglik": false,
      "female_manglik": true,
      "severity": "medium",
      "remedies": ["Perform Mangal Dosha Puja"]
    },
    "kaal_sarp_dosha": {
      "male_kaal_sarp": false,
      "female_kaal_sarp": false
    }
  },
  "recommendations": [
    "Consider performing remedial measures for Manglik Dosha",
    "Marriage timing should be carefully selected",
    "Consult an astrologer for detailed analysis"
  ],
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### 4.2 Get Marriage Matches
```http
GET /api/v1/marriage-matching/?limit=10&offset=0
Authorization: Bearer {access_token}
```

#### 4.3 Get Specific Marriage Match
```http
GET /api/v1/marriage-matching/{match_id}
Authorization: Bearer {access_token}
```

#### 4.4 Delete Marriage Match
```http
DELETE /api/v1/marriage-matching/{match_id}
Authorization: Bearer {access_token}
```

## 👨‍🏫 Astrologer Management

**Base Route:** `/api/v1/astrologers`

#### 5.1 Get All Astrologers
```http
GET /api/v1/astrologers/?specialization=marriage&language=en&min_rating=4.0&limit=10&offset=0
Authorization: Bearer {access_token}
```

**Response:**
```json
[
  {
    "astrologer_id": "astro_123",
    "name": "Dr. Rajesh Sharma",
    "email": "rajesh@example.com",
    "phone": "+919876543210",
    "bio": "Expert in Vedic astrology with 15 years experience",
    "experience_years": 15,
    "specialization": ["marriage", "career", "health"],
    "languages": ["english", "hindi", "gujarati"],
    "rating": 4.8,
    "total_reviews": 245,
    "hourly_rate": 500.0,
    "currency": "INR",
    "availability": {
      "monday": ["09:00-12:00", "14:00-18:00"],
      "tuesday": ["09:00-12:00", "14:00-18:00"]
    },
    "is_active": true,
    "is_verified": true
  }
]
```

#### 5.2 Get Specific Astrologer
```http
GET /api/v1/astrologers/{astrologer_id}
Authorization: Bearer {access_token}
```

#### 5.3 Get Astrologer Availability
```http
GET /api/v1/astrologers/availability/{astrologer_id}?date=2024-01-15
Authorization: Bearer {access_token}
```

#### 5.4 Add Astrologer Review
```http
POST /api/v1/astrologers/{astrologer_id}/reviews
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "rating": 5,
  "review": "Excellent consultation, very accurate predictions",
  "consultation_id": "consultation_id"
}
```

## 📅 Consultation Booking

**Base Route:** `/api/v1/consultations`

#### 6.1 Book Consultation
```http
POST /api/v1/consultations/book
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "astrologer_id": "astro_123",
  "profile_id": "profile_id",
  "scheduled_datetime": "2024-01-20T15:00:00Z",
  "consultation_type": "marriage",
  "specific_questions": [
    "When is the best time for marriage?",
    "What are the compatibility factors?"
  ]
}
```

**Response:**
```json
{
  "consultation_id": "consult_123",
  "user_id": "user_id",
  "astrologer_id": "astro_123",
  "profile_id": "profile_id",
  "scheduled_date_time": "2024-01-20T15:00:00Z",
  "duration_minutes": 30,
  "consultation_type": "marriage",
  "status": "pending_payment",
  "total_fee": 500.0,
  "currency": "INR",
  "payment_status": "pending",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### 6.2 Get User Consultations
```http
GET /api/v1/consultations/?status=confirmed&limit=10&offset=0
Authorization: Bearer {access_token}
```

#### 6.3 Get Specific Consultation
```http
GET /api/v1/consultations/{consultation_id}
Authorization: Bearer {access_token}
```

#### 6.4 Cancel Consultation
```http
PUT /api/v1/consultations/{consultation_id}/cancel
Authorization: Bearer {access_token}
```

#### 6.5 Complete Consultation (Astrologer)
```http
PUT /api/v1/consultations/{consultation_id}/complete
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "notes": "Detailed consultation notes and recommendations"
}
```

#### 6.6 Add Consultation Review
```http
POST /api/v1/consultations/{consultation_id}/review
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "rating": 5,
  "review": "Excellent consultation, very helpful insights"
}
```

## 💳 Payment Processing

**Base Route:** `/api/v1/payments`

#### 7.1 Create Payment Order
```http
POST /api/v1/payments/create-order
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "amount": 500.0,
  "currency": "INR",
  "service_type": "consultation",
  "reference_id": "consultation_id"
}
```

**Response:**
```json
{
  "order_id": "order_123",
  "amount": 500.0,
  "currency": "INR",
  "razorpay_order_id": "order_razorpay_123",
  "razorpay_key_id": "rzp_test_key"
}
```

#### 7.2 Verify Payment
```http 
POST /api/v1/payments/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "payment_id": "pay_razorpay_123",
  "order_id": "order_123",
  "signature": "razorpay_signature",
  "amount": 500.0,
  "currency": "INR"
}
```

**Response:**
```json
{
  "payment_verified": true,
  "payment_id": "payment_123",
  "status": "completed",
  "message": "Payment verified successfully"
}
```

#### 7.3 Get Payment History
```http
GET /api/v1/payments/history?limit=10&offset=0
Authorization: Bearer {access_token}
```

#### 7.4 Request Refund
```http
POST /api/v1/payments/refund/{payment_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "reason": "Consultation cancelled by astrologer",
  "amount": 500.0
}
```

## 🏥 Health Check

#### 8.1 Application Health
```http
GET /api/v1/health/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "firebase": "connected",
    "redis": "connected"
  }
}
```

## 🔧 Frontend Implementation Examples

### React/Next.js Integration

#### Authentication Hook
```javascript
// hooks/useAuth.js
import { useState, useEffect } from 'react';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const initiateAuth = async (identifier) => {
    const response = await fetch('/api/v1/auth/initiate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier })
    });
    return response.json();
  };

  const verifyOTP = async (sessionId, otpCode) => {
    const response = await fetch('/api/v1/auth/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_id: sessionId, 
        otp_code: otpCode 
      })
    });
    const data = await response.json();
    
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      setUser(data.user_data);
    }
    
    return data;
  };

  const logout = async () => {
    const token = localStorage.getItem('access_token');
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return { user, loading, initiateAuth, verifyOTP, logout };
};
```

#### API Service
```javascript
// services/api.js
class ZodiraAPI {
  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async request(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return response.json();
  }

  // Profile methods
  async createProfile(profileData) {
    return this.request('/api/v1/profiles/profiles', {
      method: 'POST',
      body: JSON.stringify(profileData)
    });
  }

  async getProfiles() {
    return this.request('/api/v1/profiles/profiles');
  }

  // Prediction methods
  async getDailyPrediction(profileId, date) {
    return this.request('/api/v1/predictions/daily', {
      method: 'POST',
      body: JSON.stringify({ profile_id: profileId, date })
    });
  }

  // Marriage matching methods
  async createMarriageMatch(maleProfileId, femaleProfileId) {
    return this.request('/api/v1/marriage-matching/', {
      method: 'POST',
      body: JSON.stringify({
        male_profile_id: maleProfileId,
        female_profile_id: femaleProfileId,
        matching_type: 'detailed',
        language: 'en'
      })
    });
  }

  // Consultation methods
  async bookConsultation(consultationData) {
    return this.request('/api/v1/consultations/book', {
      method: 'POST',
      body: JSON.stringify(consultationData)
    });
  }

  // Payment methods
  async createPaymentOrder(amount, serviceType, referenceId) {
    return this.request('/api/v1/payments/create-order', {
      method: 'POST',
      body: JSON.stringify({
        amount,
        currency: 'INR',
        service_type: serviceType,
        reference_id: referenceId
      })
    });
  }
}

export const api = new ZodiraAPI();
```

#### Authentication Component
```jsx
// components/AuthForm.jsx
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

export const AuthForm = () => {
  const [identifier, setIdentifier] = useState('');
  const [otp, setOtp] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [step, setStep] = useState('identifier'); // identifier, otp
  const { initiateAuth, verifyOTP } = useAuth();

  const handleInitiate = async (e) => {
    e.preventDefault();
    try {
      const result = await initiateAuth(identifier);
      setSessionId(result.session_id);
      setStep('otp');
      
      // For development - auto-fill OTP
      if (result.debug_otp) {
        setOtp(result.debug_otp);
      }
    } catch (error) {
      console.error('Auth initiation failed:', error);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    try {
      const result = await verifyOTP(sessionId, otp);
      if (result.access_token) {
        // Redirect based on next_step
        if (result.next_step === 'complete_profile') {
          router.push('/profile/create');
        } else {
          router.push('/dashboard');
        }
      }
    } catch (error) {
      console.error('OTP verification failed:', error);
    }
  };

  return (
    <div className="auth-form">
      {step === 'identifier' ? (
        <form onSubmit={handleInitiate}>
          <input
            type="text"
            placeholder="Email or Phone Number"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
          />
          <button type="submit">Send OTP</button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOTP}>
          <input
            type="text"
            placeholder="Enter OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            required
          />
          <button type="submit">Verify OTP</button>
        </form>
      )}
    </div>
  );
};
```

## 🔒 Security & Best Practices

### 1. Authentication Headers
Always include the JWT token in requests:
```javascript
headers: {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
}
```

### 2. Error Handling
```javascript
try {
  const response = await api.request('/api/v1/profiles/profiles');
} catch (error) {
  if (error.message.includes('401')) {
    // Token expired, redirect to login
    router.push('/login');
  } else if (error.message.includes('403')) {
    // Insufficient permissions
    showError('Access denied');
  } else {
    // General error
    showError('Something went wrong');
  }
}
```

### 3. Token Management
```javascript
// Check token expiry
const isTokenExpired = (token) => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
};

// Auto-refresh logic
const getValidToken = async () => {
  const token = localStorage.getItem('access_token');
  if (!token || isTokenExpired(token)) {
    // Redirect to login
    window.location.href = '/login';
    return null;
  }
  return token;
};
```

## 🚀 Deployment Configuration

### Environment Variables
```env
# Frontend .env.local
NEXT_PUBLIC_API_URL=https://api.zodira.app
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_live_key
NEXT_PUBLIC_GOOGLE_CLIENT_ID=google_client_id
```

### CORS Configuration
The backend is configured to accept requests from:
- `http://localhost:3000` (Development)
- `http://localhost:3001` (Development)
- `https://zodira.app` (Production)

## 📊 Rate Limiting

The API implements rate limiting:
- **Authentication endpoints:** 5 requests per 5 minutes per IP
- **General endpoints:** 100 requests per minute per user
- **Payment endpoints:** 10 requests per minute per user

## 🐛 Error Codes

| Code | Description | Action |
|------|-------------|--------|
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Refresh token or login |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check endpoint URL |
| 422 | Validation Error | Check request data |
| 429 | Rate Limited | Wait and retry |
| 500 | Server Error | Contact support |

## 📱 Mobile App Integration

For React Native or mobile apps, use the same API endpoints with appropriate HTTP clients:

```javascript
// React Native example
import AsyncStorage from '@react-native-async-storage/async-storage';

const api = {
  async request(endpoint, options = {}) {
    const token = await AsyncStorage.getItem('access_token');
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    });
    
    return response.json();
  }
};
```

## 🔄 Real-time Features

For real-time updates (consultation status, payment status), implement polling or WebSocket connections:

```javascript
// Polling example
const pollConsultationStatus = (consultationId) => {
  const interval = setInterval(async () => {
    try {
      const consultation = await api.request(`/api/v1/consultations/${consultationId}`);
      if (consultation.status === 'completed') {
        clearInterval(interval);
        // Handle completion
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, 5000); // Poll every 5 seconds
};
```

## 📋 Testing

### API Testing with curl
```bash
# Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/initiate" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "test@example.com"}'

# Test with authentication
curl -X GET "http://localhost:8000/api/v1/profiles/profiles" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend Testing
```javascript
// Jest test example
import { api } from '../services/api';

describe('ZODIRA API', () => {
  test('should authenticate user', async () => {
    const result = await api.initiateAuth('test@example.com');
    expect(result.session_id).toBeDefined();
    expect(result.auth_type).toBe('email');
  });
});
```

## 🎯 Complete Implementation Checklist

### Authentication Flow
- [ ] Implement login/signup form
- [ ] Handle OTP verification
- [ ] Implement Google OAuth
- [ ] Add logout functionality
- [ ] Handle token refresh
- [ ] Add session management

### User Management
- [ ] Create user profile form
- [ ] Implement profile editing
- [ ] Add person profile creation
- [ ] Handle profile validation
- [ ] Add profile deletion

### Astrology Features
- [ ] Daily prediction display
- [ ] Weekly prediction display
- [ ] Monthly prediction display
- [ ] Prediction history
- [ ] Marriage matching form
- [ ] Match results display

### Consultation System
- [ ] Astrologer listing
- [ ] Booking form
- [ ] Calendar integration
- [ ] Consultation management
- [ ] Review system

### Payment Integration
- [ ] Razorpay integration
- [ ] Payment form
- [ ] Payment verification
- [ ] Payment history
- [ ] Refund handling

### UI/UX Components
- [ ] Loading states
- [ ] Error handling
- [ ] Success messages
- [ ] Form validation
- [ ] Responsive design

This comprehensive guide provides everything needed to build a complete frontend application that integrates seamlessly with the ZODIRA backend API. All endpoints are production-ready with proper authentication, validation, and error handling.