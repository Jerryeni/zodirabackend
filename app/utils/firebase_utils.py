"""
Firestore Database Schema and Validation for ZODIRA Backend

This module defines the expected structure for all Firestore collections
and provides validation functions to ensure data consistency.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, validator
import re

# Collection Names
COLLECTIONS = {
    'users': 'users',
    'person_profiles': 'person_profiles',
    'marriage_matches': 'marriage_matches',
    'astrologers': 'astrologers',
    'consultations': 'consultations',
    'predictions': 'predictions',
    'payments': 'payments',
    'payment_orders': 'payment_orders'
}

# ============================================================================
# USERS COLLECTION SCHEMA
# ============================================================================

class UserDocument(BaseModel):
    """Schema for /users/{userId} documents"""
    userId: str
    email: Optional[str] = None
    phone: Optional[str] = None
    displayName: Optional[str] = None
    photoURL: Optional[str] = None
    emailVerified: bool = False
    phoneVerified: bool = False
    subscriptionType: str = "free"  # free, premium, pro
    language: str = "en"
    timezone: str = "Asia/Kolkata"
    createdAt: datetime
    lastLoginAt: Optional[datetime] = None
    isActive: bool = True
    preferences: Optional[Dict[str, Any]] = None
    profileComplete: bool = False
    primaryProfileId: Optional[str] = None

    @validator('subscriptionType')
    def validate_subscription_type(cls, v):
        allowed = ['free', 'premium', 'pro']
        if v not in allowed:
            raise ValueError(f'subscriptionType must be one of {allowed}')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^\+\d{10,15}$', v):
            raise ValueError('Phone must be in format +1234567890')
        return v

# ============================================================================
# PERSON PROFILES COLLECTION SCHEMA
# ============================================================================

class PersonProfileDocument(BaseModel):
    """Schema for /person_profiles/{profileId} documents"""
    id: str
    userId: str
    name: str
    birthDate: str  # ISO date string
    birthTime: str  # HH:MM:SS format
    birthPlace: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = "Asia/Kolkata"
    gender: str  # male, female, other
    profileType: str = "self"  # self, family_member, consultation

    # Calculated astrology data
    zodiacSign: Optional[str] = None
    moonSign: Optional[str] = None  # Rasi
    nakshatra: Optional[str] = None
    rashi: Optional[str] = None
    ascendant: Optional[str] = None

    # Metadata
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    isActive: bool = True

    @validator('gender')
    def validate_gender(cls, v):
        allowed = ['male', 'female', 'other']
        if v not in allowed:
            raise ValueError(f'gender must be one of {allowed}')
        return v

    @validator('profileType')
    def validate_profile_type(cls, v):
        allowed = ['self', 'family_member', 'consultation']
        if v not in allowed:
            raise ValueError(f'profileType must be one of {allowed}')
        return v

# ============================================================================
# MARRIAGE MATCHES COLLECTION SCHEMA
# ============================================================================

class MarriageMatchDocument(BaseModel):
    """Schema for /marriage_matches/{matchId} documents"""
    id: str
    maleProfileId: str
    femaleProfileId: str
    userId: str

    # Compatibility scores
    totalGunas: int
    minRequiredGunas: int = 18
    compatibilityScore: float
    compatibilityPercentage: float
    overallMatch: str

    # Detailed analysis
    gunaBreakdown: Dict[str, int]
    doshaAnalysis: Dict[str, Any]
    compatibilityDetails: Dict[str, float]
    recommendations: List[str]

    # Metadata
    matchingType: str = "detailed"  # basic, detailed, premium
    language: str = "en"
    createdAt: datetime
    expiresAt: Optional[datetime] = None

# ============================================================================
# ASTROLOGERS COLLECTION SCHEMA
# ============================================================================

class AstrologerDocument(BaseModel):
    """Schema for /astrologers/{astrologerId} documents"""
    astrologerId: str
    name: str
    email: str
    phone: str
    bio: str
    experienceYears: int
    specialization: List[str]
    languages: List[str]
    rating: float
    totalReviews: int
    hourlyRate: float
    currency: str = "INR"
    availability: Dict[str, Any]
    isActive: bool = True
    isVerified: bool = True
    createdAt: datetime

    @validator('rating')
    def validate_rating(cls, v):
        if not 0 <= v <= 5:
            raise ValueError('rating must be between 0 and 5')
        return v

# ============================================================================
# CONSULTATIONS COLLECTION SCHEMA
# ============================================================================

class ConsultationDocument(BaseModel):
    """Schema for /consultations/{consultationId} documents"""
    consultationId: str
    userId: str
    astrologerId: str
    profileId: str
    scheduledDateTime: datetime
    durationMinutes: int = 30
    timezone: str = "Asia/Kolkata"
    consultationType: str  # general, marriage, career, health
    specificQuestions: Optional[List[str]] = None
    status: str = "pending_payment"  # pending_payment, confirmed, completed, cancelled
    totalFee: float
    currency: str = "INR"
    paymentStatus: str = "pending"  # pending, completed, failed, refunded
    paymentId: Optional[str] = None
    videoRoomId: Optional[str] = None
    videoRoomUrl: Optional[str] = None
    meetingToken: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    reminderSent: bool = False

# ============================================================================
# PREDICTIONS COLLECTION SCHEMA
# ============================================================================

class PredictionDocument(BaseModel):
    """Schema for /predictions/{predictionId} documents"""
    predictionId: str
    userId: str
    profileId: str
    predictionType: str  # daily, weekly, monthly
    date: Optional[str] = None
    weekStartDate: Optional[str] = None
    month: Optional[int] = None
    year: Optional[int] = None

    # Content
    title: str
    overallPrediction: str
    career: Optional[str] = None
    loveRelationships: Optional[str] = None
    health: Optional[str] = None
    finance: Optional[str] = None

    # Lucky elements
    luckyNumbers: List[int]
    luckyColors: List[str]
    luckyDirections: Optional[List[str]] = None
    favorableTime: Optional[str] = None
    avoidTime: Optional[str] = None

    # Metadata
    generatedAt: datetime
    expiresAt: datetime
    isActive: bool = True

# ============================================================================
# PAYMENTS COLLECTION SCHEMA
# ============================================================================

class PaymentDocument(BaseModel):
    """Schema for /payments/{paymentId} documents"""
    paymentId: str
    userId: str
    consultationId: Optional[str] = None
    serviceType: str  # consultation, premium_report, subscription
    amount: float
    currency: str
    paymentMethod: str = "card"  # card, upi, wallet
    paymentGateway: str  # razorpay, stripe
    gatewayPaymentId: str
    gatewayOrderId: str
    gatewaySignature: str
    status: str  # pending, completed, failed, refunded
    failureReason: Optional[str] = None
    createdAt: datetime
    completedAt: Optional[datetime] = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_document(collection: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate document data against the appropriate schema
    """
    schema_map = {
        COLLECTIONS['users']: UserDocument,
        COLLECTIONS['person_profiles']: PersonProfileDocument,
        COLLECTIONS['marriage_matches']: MarriageMatchDocument,
        COLLECTIONS['astrologers']: AstrologerDocument,
        COLLECTIONS['consultations']: ConsultationDocument,
        COLLECTIONS['predictions']: PredictionDocument,
        COLLECTIONS['payments']: PaymentDocument,
    }

    if collection not in schema_map:
        raise ValueError(f"Unknown collection: {collection}")

    schema_class = schema_map[collection]
    validated_doc = schema_class(**data)
    return validated_doc.dict()

def create_indexes():
    """
    Define Firestore indexes needed for efficient queries
    Note: These need to be created in Firebase Console or via gcloud CLI
    """
    indexes = [
        # Users collection
        "users: email, phone, createdAt",

        # Person profiles
        "person_profiles: userId, gender, createdAt",

        # Marriage matches
        "marriage_matches: userId, createdAt, compatibilityScore",

        # Predictions
        "predictions: userId, predictionType, date, generatedAt",

        # Consultations
        "consultations: userId, astrologerId, scheduledDateTime, status",

        # Payments
        "payments: userId, status, createdAt",
    ]

    return indexes

def get_collection_config():
    """
    Return configuration for all collections including TTL policies
    """
    config = {
        COLLECTIONS['marriage_matches']: {
            'ttl_field': 'expiresAt',
            'ttl_days': 30
        },
        COLLECTIONS['predictions']: {
            'ttl_field': 'expiresAt',
            'ttl_days': 1  # daily predictions
        }
    }

    return config