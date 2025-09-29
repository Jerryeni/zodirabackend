"""
Unified Authentication Service for ZODIRA Backend

This service provides a comprehensive authentication system that handles:
- Email authentication with Google OAuth
- Phone number authentication with SMS OTP
- Unified user flow and session management
- Rate limiting and security measures
"""

import re
import json
import asyncio
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, Union, List
from enum import Enum

import httpx
import redis
from firebase_admin import auth
from google.oauth2 import id_token
from google.auth.transport import requests
from google.cloud.firestore import FieldFilter

from app.config.settings import settings
from app.config.firebase import get_firestore_client
from app.services.firebase_email_service import firebase_email_service
from app.core.security import (
    generate_secure_otp,
    create_access_token,
    validate_email,
    validate_phone_number,
    sanitize_input,
    hash_sensitive_data
)
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError
)

logger = logging.getLogger(__name__)

class AuthType(str, Enum):
    EMAIL = "email"
    PHONE = "phone"

class AuthStatus(str, Enum):
    OTP_SENT = "otp_sent"
    OTP_VERIFIED = "otp_verified"
    USER_EXISTS = "user_exists"
    NEW_USER = "new_user"
    PROFILE_REQUIRED = "profile_required"
    AUTHENTICATED = "authenticated"

class UserService:
    """Unified user service handling authentication, profiles, and user management"""
    
    def __init__(self):
        self.redis_client = self._init_redis()
        self._db = None  # Lazy initialization
        self.firebase_email = firebase_email_service
        self.rate_limit_window = 300  # 5 minutes
        self.max_otp_attempts = 3
        self.otp_expiry_minutes = 5
        # Memory storage for development
        self._memory_sessions = {}
        self._rate_limits = {}
    
    @property
    def db(self):
        """Lazy initialization of Firestore client"""
        if self._db is None:
            self._db = get_firestore_client()
        return self._db
        
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis client for session management"""
        try:
            if hasattr(settings, 'redis_url') and settings.redis_url and settings.redis_url != 'redis://localhost:6379/0':
                client = redis.from_url(settings.redis_url)
                # Test connection
                client.ping()
                logger.info("Redis connected successfully")
                return client
            else:
                logger.info("Redis not configured, using memory storage")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory storage: {e}")
        return None
    
    async def initiate_auth(self, identifier: str) -> Dict[str, Any]:
        """
        Initiate authentication process for email or phone
        
        Args:
            identifier: Email address or phone number
            
        Returns:
            Dict containing auth_type, session_id, and next_step
        """
        try:
            # Sanitize and validate input
            identifier = sanitize_input(identifier.strip().lower(), 254)
            
            if not identifier:
                raise ValidationError("Identifier cannot be empty")
            
            # Determine authentication type
            auth_type = self._determine_auth_type(identifier)
            
            # Check rate limiting
            await self._check_rate_limit(identifier)
            
            # Generate session ID
            session_id = hash_sensitive_data(f"{identifier}_{datetime.utcnow().isoformat()}")
            
            # Store session data
            session_data = {
                'identifier': identifier,
                'auth_type': auth_type.value,
                'status': AuthStatus.OTP_SENT.value,
                'created_at': datetime.utcnow().isoformat(),
                'attempts': 0,
                'max_attempts': self.max_otp_attempts
            }
            
            if auth_type == AuthType.EMAIL:
                # For email, we'll use Google OAuth or email OTP
                result = await self._initiate_email_auth(identifier, session_id, session_data)
            else:
                # For phone, send SMS OTP
                result = await self._initiate_phone_auth(identifier, session_id, session_data)
            
            logger.info(f"Authentication initiated for {auth_type.value}: {identifier}")
            return result
            
        except Exception as e:
            logger.error(f"Auth initiation failed for {identifier}: {e}")
            raise AuthenticationError(f"Authentication initiation failed: {str(e)}")
    
    def _determine_auth_type(self, identifier: str) -> AuthType:
        """Determine if identifier is email or phone number"""
        if validate_email(identifier):
            return AuthType.EMAIL
        elif validate_phone_number(identifier):
            return AuthType.PHONE
        else:
            raise ValidationError("Invalid email or phone number format")
    
    async def _check_rate_limit(self, identifier: str) -> None:
        """Check rate limiting for authentication attempts"""
        rate_limit_key = f"auth_rate_limit:{hash_sensitive_data(identifier)}"
        
        try:
            if self.redis_client:
                current_attempts = self.redis_client.get(rate_limit_key)
                if current_attempts and int(current_attempts) >= 5:  # Max 5 attempts per 5 minutes
                    raise AuthenticationError("Too many authentication attempts. Please try again later.")
                
                # Increment attempts
                pipe = self.redis_client.pipeline()
                pipe.incr(rate_limit_key)
                pipe.expire(rate_limit_key, self.rate_limit_window)
                pipe.execute()
            else:
                # Memory-based rate limiting for testing (simplified)
                if not hasattr(self, '_rate_limits'):
                    self._rate_limits = {}
                
                now = datetime.utcnow()
                if rate_limit_key in self._rate_limits:
                    attempts, last_attempt = self._rate_limits[rate_limit_key]
                    if (now - last_attempt).seconds < self.rate_limit_window and attempts >= 5:
                        raise AuthenticationError("Too many authentication attempts. Please try again later.")
                    elif (now - last_attempt).seconds >= self.rate_limit_window:
                        self._rate_limits[rate_limit_key] = (1, now)
                    else:
                        self._rate_limits[rate_limit_key] = (attempts + 1, now)
                else:
                    self._rate_limits[rate_limit_key] = (1, now)
        except AuthenticationError:
            raise
        except Exception as e:
            logger.warning(f"Rate limiting failed, allowing request: {e}")
            # Allow request to proceed if rate limiting fails
    
    async def _initiate_email_auth(self, email: str, session_id: str, session_data: Dict) -> Dict[str, Any]:
        """Initiate email authentication with OTP"""
        try:
            # Generate OTP for email
            otp_code = generate_secure_otp()
            session_data['otp_code'] = otp_code
            session_data['expires_at'] = (datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)).isoformat()
            
            # Store session
            await self._store_session(session_id, session_data)
            
            # Send email OTP (implement email service)
            await self._send_email_otp(email, otp_code)
            
            return {
                'session_id': session_id,
                'auth_type': AuthType.EMAIL.value,
                'status': AuthStatus.OTP_SENT.value,
                'message': 'OTP sent to your email address',
                'expires_in': self.otp_expiry_minutes * 60,
                'next_step': 'verify_otp',
                'identifier': email,
                'delivery_method': 'email'
            }
            
        except Exception as e:
            logger.error(f"Email auth initiation failed: {e}")
            raise AuthenticationError(f"Failed to send email OTP: {str(e)}")
    
    async def _initiate_phone_auth(self, phone: str, session_id: str, session_data: Dict) -> Dict[str, Any]:
        """Initiate phone authentication with SMS OTP"""
        try:
            # Generate OTP for phone
            otp_code = generate_secure_otp()
            session_data['otp_code'] = otp_code
            session_data['expires_at'] = (datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)).isoformat()
            
            # Store session
            await self._store_session(session_id, session_data)
            
            # Send SMS OTP
            await self._send_sms_otp(phone, otp_code)
            
            return {
                'session_id': session_id,
                'auth_type': AuthType.PHONE.value,
                'status': AuthStatus.OTP_SENT.value,
                'message': 'OTP sent to your phone number',
                'expires_in': self.otp_expiry_minutes * 60,
                'next_step': 'verify_otp',
                'identifier': phone,
                'delivery_method': 'sms'
            }
            
        except Exception as e:
            logger.error(f"Phone auth initiation failed: {e}")
            raise AuthenticationError(f"Failed to send SMS OTP: {str(e)}")
    
    async def _send_email_otp(self, email: str, otp_code: str) -> bool:
        """Send OTP via Firebase email service with enhanced debugging"""
        try:
            # Enhanced logging for debugging
            logger.info(f"Attempting to send EMAIL OTP via Firebase service")
            logger.info(f"Email: {email}")
            
            # Use Firebase email service
            success = await self.firebase_email.send_otp_email(email, otp_code)
            
            if success:
                logger.info(f"✅ EMAIL OTP sent successfully via Firebase service to {email}")
            else:
                logger.warning(f"⚠️ EMAIL OTP delivery failed, but OTP logged for testing")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ EMAIL OTP delivery failed for {email}: {e}")
            return False
        
    async def _send_sms_otp(self, raw_phone: str, otp_code: str) -> None:
        """Send OTP via SMS using MyDreams Technology API with comprehensive debugging"""

        phone = (raw_phone or "").strip()
        phone = re.sub(r"[ \-\(\)]", "", phone)

        # Handle international phone number formats
        if phone.startswith("+"):
            phone = phone[1:]  # Remove + prefix
        if phone.startswith("00"):
            phone = phone[2:]  # Remove 00 prefix

        # For Indian numbers (91 country code), remove country code to get 10-digit number
        if phone.startswith("91") and len(phone) == 12:
            phone = phone[2:]  # Remove 91 country code for Indian numbers

        # Validate final phone number format
        if not phone.isdigit() or len(phone) < 10:
            logger.error(f"❌ Invalid phone number format after processing: {phone}")
            raise ValueError(f"Invalid phone number format: {phone}")

        try:
            # Enhanced debugging logs
            logger.info(f"🔍 DEBUG: Attempting to send SMS OTP")
            logger.info(f"🔍 DEBUG: Original Phone: {raw_phone}")
            logger.info(f"🔍 DEBUG: Processed Phone: {phone}")
            logger.info(f"🔍 DEBUG: Phone Length: {len(phone)}")
            logger.info(f"🔍 DEBUG: OTP Code: {otp_code}")
            logger.info(f"🔍 DEBUG: SMS Provider: {settings.sms_provider}")
            logger.info(f"🔍 DEBUG: API URL: {settings.mydreams_api_url}")
            logger.info(f"🔍 DEBUG: API Key: {settings.mydreams_api_key[:10]}...")
            logger.info(f"🔍 DEBUG: Sender ID: {settings.mydreams_sender_id}")
            
            message = f"Use OTP {otp_code} to log in to your Account. Never share your OTP with anyone. Support contact: {settings.zodira_support_email} - My Dreams"
            
            # Prepare API request
            params = {
                'apikey': settings.mydreams_api_key,
                'senderid': settings.mydreams_sender_id,
                'number': phone, 
                'message': message
            }
            
            # Log SMS details for debugging
            logger.info(f"SMS OTP delivery details - Phone: {phone}, OTP: {otp_code}")
            
            logger.info(f"🔍 DEBUG: SMS API Request params: {params}")
            
            # Try to send via API
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    logger.info(f"🔍 DEBUG: Making HTTP request to SMS API")
                    response = await client.get(settings.mydreams_api_url, params=params)
                    
                    logger.info(f"🔍 DEBUG: SMS API Response Status: {response.status_code}")
                    logger.info(f"🔍 DEBUG: SMS API Response Text: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.text.strip()
                        if 'success' in result.lower() or 'sent' in result.lower():
                            logger.info(f"✅ SMS OTP sent successfully to {phone}")
                        else:
                            logger.warning(f"⚠️ SMS API returned unexpected response: {result}")
                    else:
                        logger.warning(f"⚠️ SMS API HTTP error: {response.status_code}")
                        
            except Exception as api_error:
                logger.warning(f"⚠️ SMS API call failed: {api_error}")
            
            # Always log success for development testing
            # logger.info(f"✅ SMS OTP process completed for {phone}")
                    
        except Exception as e:
            logger.error(f"❌ SMS OTP delivery failed for {phone}: {e}")
            raise AuthenticationError(f"SMS OTP delivery failed: {str(e)}")
    
    async def verify_otp(self, session_id: str, otp_code: str) -> Dict[str, Any]:
        """
        Verify OTP and proceed with authentication flow
        
        Args:
            session_id: Session identifier
            otp_code: OTP code entered by user
            
        Returns:
            Dict containing authentication result and next steps
        """
        try:
            # Retrieve session data
            session_data = await self._get_session(session_id)
            if not session_data:
                raise AuthenticationError("Invalid or expired session")
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'])
            if datetime.utcnow() > expires_at:
                await self._delete_session(session_id)
                raise AuthenticationError("OTP has expired")
            
            # Check attempt limit
            if session_data['attempts'] >= session_data['max_attempts']:
                await self._delete_session(session_id)
                raise AuthenticationError("Maximum OTP attempts exceeded")
            
            # Verify OTP
            if session_data['otp_code'] != otp_code:
                session_data['attempts'] += 1
                await self._store_session(session_id, session_data)
                remaining_attempts = session_data['max_attempts'] - session_data['attempts']
                raise AuthenticationError(f"Invalid OTP. {remaining_attempts} attempts remaining.")
            
            # OTP verified successfully
            identifier = session_data['identifier']
            auth_type = session_data['auth_type']
            
            # Check if user exists
            user_data = await self._get_or_create_user(identifier, auth_type)
            
            # Generate JWT token
            token_data = {
                'sub': user_data['uid'],
                'email': user_data.get('email'),
                'phone': user_data.get('phone'),
                'auth_type': auth_type
            }
            access_token = create_access_token(token_data)
            
            # Update session status
            session_data['status'] = AuthStatus.AUTHENTICATED.value
            session_data['user_id'] = user_data['uid']
            await self._store_session(session_id, session_data)

            # Create persistent session for automatic login
            persistent_session = await self.create_persistent_session(user_data['uid'])

            # Determine next step based on user profile
            next_step = await self._determine_next_step(user_data['uid'])

            result = {
                'session_id': session_id,
                'access_token': access_token,
                'persistent_session_token': persistent_session.get('session_token'),
                'user_id': user_data['uid'],
                'status': AuthStatus.AUTHENTICATED.value,
                'is_new_user': user_data.get('is_new_user', False),
                'next_step': next_step,
                'user_data': {
                    'uid': user_data['uid'],
                    'email': user_data.get('email'),
                    'phone': user_data.get('phone'),
                    'display_name': user_data.get('display_name'),
                    'profile_complete': user_data.get('profile_complete', False)
                }
            }
            
            logger.info(f"OTP verified successfully for user: {user_data['uid']}")
            return result
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"OTP verification failed: {e}")
            raise AuthenticationError(f"OTP verification failed: {str(e)}")
    
    async def _get_or_create_user(self, identifier: str, auth_type: str) -> Dict[str, Any]:
        """Get existing user or create new user"""
        try:
            user_record = None
            is_new_user = False
            
            # Try to find existing user
            if auth_type == AuthType.EMAIL.value:
                try:
                    user_record = auth.get_user_by_email(identifier)
                except auth.UserNotFoundError:
                    pass
            else:  # phone
                try:
                    users = auth.get_users([auth.PhoneIdentifier(identifier)])
                    if users.users:
                        user_record = users.users[0]
                except Exception:
                    pass
            
            # Create new user if not found
            if not user_record:
                if auth_type == AuthType.EMAIL.value:
                    user_record = auth.create_user(email=identifier)
                else:
                    user_record = auth.create_user(phone_number=identifier)
                is_new_user = True
                logger.info(f"New user created: {user_record.uid}")
            
            # Get or create user profile in Firestore
            profile_data = await self._get_or_create_user_profile(user_record, is_new_user)
            
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'phone': user_record.phone_number,
                'display_name': user_record.display_name,
                'is_new_user': is_new_user,
                'profile_complete': profile_data.get('profile_complete', False)
            }
            
        except Exception as e:
            logger.error(f"User creation/retrieval failed: {e}")
            raise AuthenticationError(f"User processing failed: {str(e)}")
    
    async def _get_or_create_user_profile(self, user_record, is_new_user: bool, google_id: str = None) -> Dict[str, Any]:
        """Get or create user profile in Firestore"""
        try:
            user_ref = self.db.collection('users').document(user_record.uid)
            user_doc = user_ref.get()

            if not user_doc.exists or is_new_user:
                # Create new user profile
                # For Google OAuth users, mark as complete since they provided info via Google
                is_google_auth = google_id is not None
                profile_data = {
                    'userId': user_record.uid,
                    'email': user_record.email,
                    'phone': user_record.phone_number,
                    'displayName': user_record.display_name,
                    'createdAt': datetime.utcnow(),
                    'lastLoginAt': datetime.utcnow(),
                    'isActive': True,
                    'subscriptionType': 'free',
                    'language': 'en',
                    'timezone': 'Asia/Kolkata',
                    'profile_complete': is_google_auth,  # Google OAuth users are considered complete
                    'emailVerified': user_record.email_verified if user_record.email else False,
                    'phoneVerified': True if user_record.phone_number else False,
                    # Add persistent session fields
                    'persistent_session_enabled': True,
                    'session_expires_at': None,
                    'refresh_token': None,
                }
                if google_id:
                    profile_data['google_id'] = google_id

                user_ref.set(profile_data)
                logger.info(f"User profile created for: {user_record.uid}")
                return profile_data
            else:
                # Update last login and google_id if it's missing
                profile_data = user_doc.to_dict()
                update_data = {'lastLoginAt': datetime.utcnow()}
                if google_id and 'google_id' not in profile_data:
                    update_data['google_id'] = google_id
                user_ref.update(update_data)
                return profile_data

        except Exception as e:
            logger.error(f"User profile processing failed: {e}")
            return {'profile_complete': False}
    
    async def _determine_next_step(self, user_id: str) -> str:
        """Determine next step in user flow"""
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                profile_complete = user_data.get('profile_complete', False)

                # Also check if user has any active profiles
                if not profile_complete:
                    profiles_query = self.db.collection('person_profiles').where(filter=FieldFilter('user_id', '==', user_id)).where(filter=FieldFilter('is_active', '==', True)).limit(1)
                    has_profiles = len(profiles_query.get()) > 0
                    if has_profiles:
                        # If has profiles but flag not set, update the flag
                        user_ref.update({'profile_complete': True})
                        return 'dashboard'

                if profile_complete:
                    return 'dashboard'
                else:
                    return 'complete_profile'
            else:
                return 'complete_profile'

        except Exception as e:
            logger.error(f"Next step determination failed: {e}")
            return 'complete_profile'
    
    async def google_oauth_login(self, id_token_str: str) -> Dict[str, Any]:
        """Handle Google OAuth login"""
        try:
            # Verify Google ID token
            id_info = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                settings.google_client_id
            )
            
            if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise AuthenticationError('Invalid token issuer')
            
            email = id_info['email']
            name = id_info.get('name', '')
            
            # Get or create Firebase user
            try:
                user_record = auth.get_user_by_email(email)
                is_new_user = False
            except auth.UserNotFoundError:
                user_record = auth.create_user(
                    email=email,
                    display_name=name,
                    email_verified=True
                )
                is_new_user = True
            
            # Create user profile
            profile_data = await self._get_or_create_user_profile(user_record, is_new_user)

            # Create persistent session for automatic login
            persistent_session = await self.create_persistent_session(user_record.uid)

            # Generate JWT token
            token_data = {
                'sub': user_record.uid,
                'email': user_record.email,
                'auth_type': AuthType.EMAIL.value
            }
            access_token = create_access_token(token_data)

            # Determine next step
            next_step = await self._determine_next_step(user_record.uid)

            result = {
                'access_token': access_token,
                'persistent_session_token': persistent_session.get('session_token'),
                'user_id': user_record.uid,
                'status': AuthStatus.AUTHENTICATED.value,
                'is_new_user': is_new_user,
                'next_step': next_step,
                'user_data': {
                    'uid': user_record.uid,
                    'email': user_record.email,
                    'display_name': user_record.display_name,
                    'profile_complete': profile_data.get('profile_complete', False)
                }
            }
            
            logger.info(f"Google OAuth login successful for: {user_record.uid}")
            return result
            
        except Exception as e:
            logger.error(f"Google OAuth login failed: {e}")
            raise AuthenticationError(f"Google OAuth login failed: {str(e)}")

    async def handle_google_user(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user login or creation from Google OAuth data.
        """
        try:
            google_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name")
            picture = user_info.get("picture")

            if not email:
                raise AuthenticationError("Email not provided by Google")

            # Check if user exists with this Google ID
            user_record = None
            try:
                # Firestore does not support querying by custom claims, so we query our 'users' collection
                users_ref = self.db.collection('users')
                query = users_ref.where(filter=FieldFilter('google_id', '==', google_id)).limit(1)
                docs = query.stream()
                user_doc = next(docs, None)

                if user_doc:
                    user_record = auth.get_user(user_doc.id)

            except Exception:
                pass  # User not found by google_id

            is_new_user = False
            # If not found by google_id, check by email
            if not user_record:
                try:
                    user_record = auth.get_user_by_email(email)
                    # If user exists, just update the Google ID in our custom collection
                    # Note: Provider linking requires client-side operation, not admin SDK
                    self.db.collection('users').document(user_record.uid).update({'google_id': google_id})

                except auth.UserNotFoundError:
                    # Create new user if not found by either
                    user_record = auth.create_user(
                        email=email,
                        email_verified=True,
                        display_name=name,
                        photo_url=picture,
                    )
                    is_new_user = True
            
            # Get or create user profile in Firestore
            profile_data = await self._get_or_create_user_profile(user_record, is_new_user, google_id)

            # Create persistent session for automatic login
            persistent_session = await self.create_persistent_session(user_record.uid)

            # Generate JWT token
            token_data = {
                'sub': user_record.uid,
                'email': user_record.email,
                'auth_type': 'google'
            }
            access_token = create_access_token(token_data)

            # Determine next step
            next_step = await self._determine_next_step(user_record.uid)

            return {
                'session_id': hash_sensitive_data(f"{email}_{datetime.utcnow().isoformat()}"),
                'access_token': access_token,
                'persistent_session_token': persistent_session.get('session_token'),
                'user_id': user_record.uid,
                'status': AuthStatus.AUTHENTICATED.value,
                'is_new_user': is_new_user,
                'next_step': next_step,
                'user_data': {
                    'uid': user_record.uid,
                    'email': user_record.email,
                    'display_name': user_record.display_name,
                    'profile_complete': profile_data.get('profile_complete', False)
                }
            }

        except Exception as e:
            logger.error(f"Google user handling failed: {e}")
            raise AuthenticationError(f"Google user processing failed: {str(e)}")
    
    async def logout(self, session_id: str, user_id: str, persistent_session_token: str = None) -> Dict[str, Any]:
        """Logout user and invalidate session"""
        try:
            # Delete current session
            await self._delete_session(session_id)

            # Invalidate persistent session if provided
            if persistent_session_token:
                await self.invalidate_persistent_session(user_id, persistent_session_token)

            # Revoke Firebase tokens
            auth.revoke_refresh_tokens(user_id)

            logger.info(f"User logged out: {user_id}")
            return {'message': 'Logged out successfully'}

        except Exception as e:
            logger.error(f"Logout failed: {e}")
            raise AuthenticationError(f"Logout failed: {str(e)}")
    
    async def _store_session(self, session_id: str, session_data: Dict) -> None:
        """Store session data"""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    f"auth_session:{session_id}",
                    self.otp_expiry_minutes * 60,
                    json.dumps(session_data, default=str)
                )
                logger.debug(f"Session stored in Redis: {session_id}")
            else:
                # Fallback to in-memory storage for testing
                if not hasattr(self, '_memory_sessions'):
                    self._memory_sessions = {}
                self._memory_sessions[session_id] = session_data
                logger.debug(f"Session stored in memory: {session_id}")
        except Exception as e:
            logger.warning(f"Session storage failed, using memory fallback: {e}")
            # Fallback to memory storage
            if not hasattr(self, '_memory_sessions'):
                self._memory_sessions = {}
            self._memory_sessions[session_id] = session_data
    
    async def _get_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve session data"""
        try:
            if self.redis_client:
                session_data = self.redis_client.get(f"auth_session:{session_id}")
                if session_data:
                    return json.loads(session_data)
            else:
                # Fallback to in-memory storage
                if hasattr(self, '_memory_sessions'):
                    return self._memory_sessions.get(session_id)
            return None
        except Exception as e:
            logger.error(f"Session retrieval failed: {e}")
            return None
    
    async def _delete_session(self, session_id: str) -> None:
        """Delete session data"""
        try:
            if self.redis_client:
                self.redis_client.delete(f"auth_session:{session_id}")
            else:
                # Fallback to in-memory storage
                if hasattr(self, '_memory_sessions'):
                    self._memory_sessions.pop(session_id, None)
        except Exception as e:
            logger.error(f"Session deletion failed: {e}")

    async def create_persistent_session(self, user_id: str, session_duration_days: int = 30) -> Dict[str, Any]:
        """
        Create a persistent session for automatic login

        Args:
            user_id: User ID to create session for
            session_duration_days: How long session should last

        Returns:
            Dict containing session information
        """
        try:
            # Generate persistent session token
            session_token = hash_sensitive_data(f"{user_id}_{datetime.utcnow().isoformat()}_{secrets.token_urlsafe(32)}")
            expires_at = datetime.utcnow() + timedelta(days=session_duration_days)

            # Store session in Firestore
            session_ref = self.db.collection('user_sessions').document(session_token)
            session_data = {
                'user_id': user_id,
                'session_token': session_token,
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'is_active': True,
                'last_accessed': datetime.utcnow(),
                'device_info': 'web_app',  # Can be extended to track device info
                'ip_address': None  # Can be extended to track IP
            }

            session_ref.set(session_data)

            # Update user profile with session info
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'persistent_session_enabled': True,
                'session_expires_at': expires_at,
                'last_session_token': session_token
            })

            logger.info(f"Created persistent session for user: {user_id}")
            return {
                'session_token': session_token,
                'expires_at': expires_at.isoformat(),
                'user_id': user_id
            }

        except Exception as e:
            logger.error(f"Failed to create persistent session for user {user_id}: {e}")
            raise AuthenticationError(f"Failed to create persistent session: {str(e)}")

    async def validate_persistent_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate persistent session token

        Args:
            session_token: Session token to validate

        Returns:
            User data if session is valid, None otherwise
        """
        try:
            if not session_token:
                return None

            # Get session from Firestore
            session_ref = self.db.collection('user_sessions').document(session_token)
            session_doc = session_ref.get()

            if not session_doc.exists:
                logger.warning(f"Session not found: {session_token}")
                return None

            session_data = session_doc.to_dict()

            # Check if session is active
            if not session_data.get('is_active', False):
                logger.info(f"Inactive session accessed: {session_token}")
                return None

            # Check if session is expired
            expires_at = session_data.get('expires_at')
            if expires_at:
                try:
                    # Handle different datetime formats
                    if isinstance(expires_at, str):
                        if expires_at.endswith('Z'):
                            expires_at_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        else:
                            expires_at_dt = datetime.fromisoformat(expires_at)
                    else:
                        # Assume it's already a datetime object
                        expires_at_dt = expires_at

                    if expires_at_dt < datetime.utcnow().replace(tzinfo=expires_at_dt.tzinfo) if expires_at_dt.tzinfo else datetime.utcnow():
                        logger.info(f"Expired session accessed: {session_token}")
                        # Mark session as inactive
                        session_ref.update({'is_active': False})
                        return None
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid expires_at format for session {session_token}: {e}")
                    # Mark session as inactive if we can't parse the expiration
                    session_ref.update({'is_active': False})
                    return None

            user_id = session_data.get('user_id')
            if not user_id:
                logger.warning(f"Session missing user_id: {session_token}")
                return None

            # Get user data
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()

            if not user_doc.exists:
                logger.warning(f"User not found for session: {user_id}")
                return None

            user_data = user_doc.to_dict()

            # Check if user is active
            if not user_data.get('isActive', False):
                logger.info(f"Inactive user session accessed: {user_id}")
                return None

            # Update last accessed time
            session_ref.update({'last_accessed': datetime.utcnow()})

            # Generate new JWT token
            token_data = {
                'sub': user_id,
                'email': user_data.get('email'),
                'phone': user_data.get('phone'),
                'auth_type': 'persistent_session'
            }
            access_token = create_access_token(token_data)

            logger.info(f"Valid persistent session for user: {user_id}")
            return {
                'access_token': access_token,
                'user_id': user_id,
                'user_data': user_data,
                'session_token': session_token
            }

        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None

    async def invalidate_persistent_session(self, user_id: str, session_token: str = None) -> bool:
        """
        Invalidate persistent session(s)

        Args:
            user_id: User ID
            session_token: Specific session to invalidate, or None for all user sessions

        Returns:
            True if successful
        """
        try:
            if session_token:
                # Invalidate specific session
                session_ref = self.db.collection('user_sessions').document(session_token)
                session_ref.update({
                    'is_active': False,
                    'invalidated_at': datetime.utcnow()
                })
            else:
                # Invalidate all user sessions
                sessions_ref = self.db.collection('user_sessions')
                user_sessions = sessions_ref.where('user_id', '==', user_id).where('is_active', '==', True).stream()

                for session_doc in user_sessions:
                    session_doc.reference.update({
                        'is_active': False,
                        'invalidated_at': datetime.utcnow()
                    })

            # Update user profile
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'persistent_session_enabled': False,
                'session_expires_at': None,
                'last_session_token': None
            })

            logger.info(f"Invalidated persistent session(s) for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to invalidate session for user {user_id}: {e}")
            return False

    async def refresh_persistent_session(self, user_id: str) -> Optional[str]:
        """
        Refresh persistent session expiration

        Args:
            user_id: User ID

        Returns:
            New session token or None if failed
        """
        try:
            # Invalidate existing sessions
            await self.invalidate_persistent_session(user_id)

            # Create new session
            session_data = await self.create_persistent_session(user_id)
            return session_data.get('session_token')

        except Exception as e:
            logger.error(f"Failed to refresh session for user {user_id}: {e}")
            return None

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user

        Args:
            user_id: User ID

        Returns:
            List of session data
        """
        try:
            sessions_ref = self.db.collection('user_sessions')
            sessions = sessions_ref.where('user_id', '==', user_id).where('is_active', '==', True).stream()

            session_list = []
            for session_doc in sessions:
                session_data = session_doc.to_dict()
                session_list.append({
                    'session_token': session_doc.id,
                    'created_at': session_data.get('created_at'),
                    'expires_at': session_data.get('expires_at'),
                    'last_accessed': session_data.get('last_accessed'),
                    'device_info': session_data.get('device_info')
                })

            return session_list

        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []

    async def check_persistent_login(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Check for valid persistent session on app startup

        Args:
            session_token: Persistent session token from client storage

        Returns:
            User authentication data if session is valid, None otherwise
        """
        try:
            if not session_token:
                return None

            # Validate the persistent session
            session_data = await self.validate_persistent_session(session_token)

            if session_data:
                # Determine next step for the user
                next_step = await self._determine_next_step(session_data['user_id'])

                # Update last login time in user profile
                user_ref = self.db.collection('users').document(session_data['user_id'])
                user_ref.update({'lastLoginAt': datetime.utcnow()})

                logger.info(f"Persistent login successful for user: {session_data['user_id']}")
                return {
                    'access_token': session_data['access_token'],
                    'user_id': session_data['user_id'],
                    'user_data': session_data['user_data'],
                    'next_step': next_step,
                    'persistent_session_token': session_token
                }
            else:
                logger.info("Persistent session invalid or expired")
                return None

        except Exception as e:
            logger.error(f"Persistent login check failed: {e}")
            return None

# Global service instance
user_service = UserService()