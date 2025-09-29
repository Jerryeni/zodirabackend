"""
Authentication Service for ZODIRA Backend

This service provides authentication functions for the legacy auth endpoints.
"""

import logging
from typing import Dict, Any, Optional
from firebase_admin import auth
from app.core.security import verify_token
from app.services.user_service import user_service
from app.config.firebase import get_firestore_client
from datetime import datetime

logger = logging.getLogger(__name__)

async def create_user(email: str, password: str) -> auth.UserRecord:
    """Create a new user with email and password"""
    try:
        user = auth.create_user(email=email, password=password)
        logger.info(f"User created: {user.uid}")
        return user
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise

async def create_phone_user(phone_number: str) -> auth.UserRecord:
    """Create a new user with phone number"""
    try:
        user = auth.create_user(phone_number=phone_number)
        logger.info(f"Phone user created: {user.uid}")
        return user
    except Exception as e:
        logger.error(f"Failed to create phone user: {e}")
        raise

async def send_phone_verification(phone_number: str) -> str:
    """Send phone verification code"""
    try:
        # Use the user service to initiate phone auth
        result = await user_service.initiate_auth(phone_number)

        # Extract verification_id (session_id) from result
        verification_id = result.get('session_id')
        if not verification_id:
            raise Exception("No verification ID returned")

        logger.info(f"Phone verification sent to: {phone_number}")
        return verification_id
    except Exception as e:
        logger.error(f"Failed to send phone verification: {e}")
        raise

async def verify_phone_code(verification_id: str, verification_code: str) -> Dict[str, Any]:
    """Verify phone code and return user info"""
    try:
        # Use the user service to verify OTP
        result = await user_service.verify_otp(verification_id, verification_code)

        # Get user record from Firebase
        user_record = auth.get_user(result['user_id'])

        return {
            'uid': user_record.uid,
            'phone_number': user_record.phone_number,
            'is_new_user': result.get('is_new_user', False)
        }
    except Exception as e:
        logger.error(f"Failed to verify phone code: {e}")
        raise

async def initialize_user_profile(uid: str, email: str = None, phone: str = None, display_name: str = None):
    """Initialize user profile in Firestore after authentication"""
    try:
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
            logger.info(f"User profile initialized: {uid}")
        else:
            logger.info(f"User profile already exists: {uid}")
    except Exception as e:
        logger.error(f"Failed to initialize user profile: {e}")
        raise