"""
Unified Authentication API Endpoints for ZODIRA Backend

This router exposes the unified authentication flows (email/phone OTP, Google OAuth)
under /api/v1/auth, backed by Firestore for sessions and rate limits.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, validator, Field
from typing import Optional, Dict, Any, List
import logging
import json
from urllib.parse import urlencode
import secrets
import httpx

from app.services.user_service import user_service, AuthStatus
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationError, ValidationError
from app.config.settings import settings
from app.config.firebase import get_firestore_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

# Request Models
class AuthInitiateRequest(BaseModel):
    identifier: str  # Email or phone number (E.164 for phone)

    @validator('identifier')
    def validate_identifier(cls, v):
        if not v or not v.strip():
            raise ValueError('Identifier cannot be empty')
        return v.strip().lower()

class OTPVerifyRequest(BaseModel):
    session_id: str
    otp_code: str

    @validator('session_id')
    def validate_session_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid session ID')
        return v.strip()

    @validator('otp_code')
    def validate_otp_code(cls, v):
        if not v or not v.isdigit() or len(v) != 6:
            raise ValueError('OTP must be a 6-digit number')
        return v

class GoogleOAuthRequest(BaseModel):
    id_token: str

    @validator('id_token')
    def validate_id_token(cls, v):
        if not v or len(v) < 100:
            raise ValueError('Invalid Google ID token')
        return v

class LogoutRequest(BaseModel):
    session_id: Optional[str] = None

# Response Models
class AuthInitiateResponse(BaseModel):
    session_id: str
    auth_type: str
    status: str
    message: str
    expires_in: int
    next_step: str

class AuthVerifyResponse(BaseModel):
    session_id: str
    access_token: str
    user_id: str
    status: str
    is_new_user: bool
    next_step: str
    user_data: dict

class GoogleOAuthResponse(BaseModel):
    access_token: str
    user_id: str
    status: str
    is_new_user: bool
    next_step: str
    user_data: dict

class LogoutResponse(BaseModel):
    message: str

def _mask_identifier(identifier: str, auth_type: str) -> str:
    if auth_type == "email":
        parts = identifier.split('@')
        if len(parts) == 2:
            username, domain = parts
            masked_username = username[:2] + '*' * max(0, len(username) - 2)
            return f"{masked_username}@{domain}"
    else:
        if len(identifier) > 6:
            return identifier[:3] + '*' * (len(identifier) - 6) + identifier[-3:]
    return identifier

async def _track_user_login(user_id: str, is_new_user: bool):
    try:
        logger.info(f"User login tracked: {user_id}, new_user: {is_new_user}")
    except Exception as e:
        logger.error(f"User login tracking failed: {e}")

@router.post("/initiate", response_model=AuthInitiateResponse)
async def initiate_authentication(request: AuthInitiateRequest, background_tasks: BackgroundTasks):
    try:
        result = await user_service.initiate_auth(request.identifier)
        auth_type = "email" if "@" in request.identifier else "phone"
        masked = _mask_identifier(request.identifier, auth_type)
        logger.info(f"Authentication initiated for {auth_type}: {masked}")
        return AuthInitiateResponse(**result)
    except ValidationError as e:
        logger.warning(f"Validation error in auth initiation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AuthenticationError as e:
        logger.warning(f"Authentication error in auth initiation: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in auth initiation: {e}")
        raise HTTPException(status_code=500, detail="Authentication initiation failed")

@router.post("/verify-otp", response_model=AuthVerifyResponse)
async def verify_otp(request: OTPVerifyRequest, background_tasks: BackgroundTasks):
    try:
        result = await user_service.verify_otp(request.session_id, request.otp_code)
        logger.info(f"OTP verification successful for user: {result['user_id']}")
        background_tasks.add_task(_track_user_login, result['user_id'], result['is_new_user'])
        return AuthVerifyResponse(**result)
    except AuthenticationError as e:
        logger.warning(f"OTP verification failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in OTP verification: {e}")
        raise HTTPException(status_code=500, detail="OTP verification failed")

@router.post("/google-oauth", response_model=GoogleOAuthResponse)
async def google_oauth_login(request: GoogleOAuthRequest, background_tasks: BackgroundTasks):
    try:
        # Guard: Only allow when Google OAuth is configured
        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(status_code=503, detail="Google OAuth not configured")

        result = await user_service.google_oauth_login(request.id_token)
        logger.info(f"Google OAuth login successful for user: {result['user_id']}")
        background_tasks.add_task(_track_user_login, result['user_id'], result['is_new_user'])
        return GoogleOAuthResponse(**result)
    except AuthenticationError as e:
        logger.warning(f"Google OAuth login failed: {e}")
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google OAuth: {e}")
        raise HTTPException(status_code=500, detail="Google OAuth login failed")

@router.get("/google/login")
async def google_login():
    # Guard: Only expose login URL when configured
    if not settings.google_client_id or not settings.redirect_uri:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    google_login_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"url": google_login_url}

@router.get("/google/callback")
async def google_callback(code: str, state: str, background_tasks: BackgroundTasks):
    # Guard: Only process callback when configured
    if not settings.google_client_id or not settings.google_client_secret or not settings.redirect_uri:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    logger.info(f"GOOGLE OAUTH CALLBACK: code_len={len(code) if code else 0}, state={state}")
    logger.info(f"Configured redirect_uri: {settings.redirect_uri}")
    logger.info(f"Configured frontend_url: {settings.frontend_url}")
    async with httpx.AsyncClient() as client:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "redirect_uri": settings.redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = await client.post(token_url, data=token_data)
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.status_code} {token_response.text}")
            return {"error": "google_auth_failed", "status": token_response.status_code}
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = await client.get(userinfo_url, headers=headers)
        if userinfo_response.status_code != 200:
            logger.error(f"Userinfo fetch failed: {userinfo_response.status_code} {userinfo_response.text}")
            return {"error": "google_user_info_failed", "status": userinfo_response.status_code}
        user_info = userinfo_response.json()
        try:
            result = await user_service.handle_google_user(user_info)
        except Exception as e:
            logger.error(f"User processing failed: {e}")
            return {"error": "google_user_processing_failed", "details": str(e)}
        background_tasks.add_task(_track_user_login, result['user_id'], result['is_new_user'])
        return {
            "access_token": result["access_token"],
            "user": result["user_data"],
            "is_new_user": result["is_new_user"],
            "next_step": result["next_step"],
        }

@router.post("/logout", response_model=LogoutResponse)
async def logout(request: LogoutRequest, current_user: str = Depends(get_current_user)):
    try:
        session_id = request.session_id or "unknown"
        result = await user_service.logout(session_id, current_user)
        logger.info(f"User logged out: {current_user}")
        return LogoutResponse(**result)
    except Exception as e:
        logger.error(f"Logout failed for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/health")
async def auth_health_check():
    try:
        # Basic Firestore connectivity check
        db = get_firestore_client()
        list(db.collections())  # light call
        return {
            "status": "healthy",
            "firebase": "connected",
        }
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        raise HTTPException(status_code=503, detail="Authentication service unhealthy")