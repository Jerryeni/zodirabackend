from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from firebase_admin import auth
from pydantic import BaseModel
from app.services.auth_service import create_user, verify_token, create_phone_user, send_phone_verification, verify_phone_code
from app.schemas.auth import UserCreate
from app.config.firebase import get_firestore_client
from app.core.dependencies import get_current_user
from datetime import datetime
from typing import Optional

router = APIRouter(tags=["authentication"])

# Request/Response Models
class TokenRequest(BaseModel):
    id_token: str

class RegisterResponse(BaseModel):
    uid: str
    email: str

class LoginResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None

class PhoneAuthRequest(BaseModel):
    phone_number: str  # Format: +91xxxxxxxxxx

class PhoneVerificationRequest(BaseModel):
    phone_number: str
    verification_code: str

class PhoneVerificationResponse(BaseModel):
    verification_id: str
    message: str

class PhoneLoginResponse(BaseModel):
    uid: str
    phone: str
    is_new_user: bool

# # Email/Password Authentication
# @router.post("/register", response_model=RegisterResponse)
# async def register(user: UserCreate):
#     try:
#         firebase_user = create_user(user.email, user.password)
#         return RegisterResponse(uid=firebase_user.uid, email=firebase_user.email)
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @router.post("/login", response_model=LoginResponse)
# async def login(request: TokenRequest):
#     try:
#         decoded_token = verify_token(request.id_token)
#         uid = decoded_token['uid']
#         user = auth.get_user(uid)
#         return LoginResponse(
#             uid=user.uid,
#             email=user.email,
#             phone=user.phone_number,
#             display_name=user.display_name
#         )
#     except Exception as e:
#         raise HTTPException(status_code=401, detail="Invalid token")

# Phone Authentication
@router.post("/phone/send-verification", response_model=PhoneVerificationResponse)
async def send_phone_verification_code(request: PhoneAuthRequest, background_tasks: BackgroundTasks):
    """Send OTP to phone number for verification"""
    try:
        verification_id = await send_phone_verification(request.phone_number)
        background_tasks.add_task(store_verification_attempt, request.phone_number, verification_id)
        return PhoneVerificationResponse(
            verification_id=verification_id,
            message="Verification code sent to your phone"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send verification code: {str(e)}")

@router.post("/phone/verify", response_model=PhoneLoginResponse)
async def verify_phone_code(request: PhoneVerificationRequest):
    """Verify OTP and authenticate user"""
    try:
        # Verify the code with Firebase
        result = await verify_phone_code(request.verification_id, request.verification_code)

        uid = result['uid']
        phone = result['phone_number']
        is_new_user = result['is_new_user']

        # If new user, create profile in Firestore
        if is_new_user:
            await initialize_user_profile(uid, phone=phone)

        return PhoneLoginResponse(
            uid=uid,
            phone=phone,
            is_new_user=is_new_user
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Verification failed: {str(e)}")

@router.post("/phone/register")
async def register_with_phone(request: PhoneVerificationRequest):
    """Complete phone registration after OTP verification"""
    try:
        result = await verify_phone_code(request.verification_id, request.verification_code)
        uid = result['uid']
        phone = result['phone_number']

        # Initialize user profile
        await initialize_user_profile(uid, phone=phone)

        return {"message": "Phone registration completed", "uid": uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")

# OAuth Authentication (Google, Facebook)
@router.post("/oauth/login", response_model=LoginResponse)
async def oauth_login(request: TokenRequest):
    """Handle OAuth login (Google, Facebook)"""
    try:
        decoded_token = verify_token(request.id_token)
        uid = decoded_token['uid']
        user = auth.get_user(uid)

        # Initialize user profile if new
        await initialize_user_profile(uid, email=user.email, display_name=user.display_name)

        return LoginResponse(
            uid=user.uid,
            email=user.email,
            phone=user.phone_number,
            display_name=user.display_name
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="OAuth authentication failed")

# Token Verification
@router.post("/verify-token", response_model=LoginResponse)
async def verify_token_endpoint(request: TokenRequest):
    return await login(request)

@router.post("/logout")
async def logout():
    # Logout is typically handled client-side
    return {"message": "Logged out successfully"}

# Helper Functions
async def initialize_user_profile(uid: str, email: str = None, phone: str = None, display_name: str = None):
    """Initialize user profile in Firestore after authentication"""
    db = get_firestore_client()
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        user_data = {
            'userId': uid,
            'createdAt': datetime.utcnow(),
            'isActive': True,
            'subscriptionType': 'free',
            'language': 'en',
            'timezone': 'Asia/Kolkata'
        }

        if email:
            user_data['email'] = email
        if phone:
            user_data['phone'] = phone
        if display_name:
            user_data['displayName'] = display_name

        user_ref.set(user_data)

async def store_verification_attempt(phone_number: str, verification_id: str):
    """Store phone verification attempt for rate limiting"""
    # Implementation for rate limiting can be added here
    pass