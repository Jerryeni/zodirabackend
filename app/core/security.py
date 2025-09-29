from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config.settings import settings
import secrets
import hashlib
import logging
import re
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)

# Password context with secure configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increased rounds for better security
)

# Token blacklist (in production, use Redis)
_token_blacklist: Set[str] = set()

class TokenData(BaseModel):
    """Token data validation model"""
    sub: str
    exp: int
    iat: int
    jti: Optional[str] = None
    
    @validator('sub')
    def validate_subject(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Invalid token subject')
        return v

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash with timing attack protection"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate secure password hash with validation"""
    if not validate_password_strength(password):
        raise ValueError("Password does not meet security requirements")
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> bool:
    """Validate password meets security requirements"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):  # Uppercase letter
        return False
    if not re.search(r'[a-z]', password):  # Lowercase letter
        return False
    if not re.search(r'\d', password):     # Digit
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Special char
        return False
    return True

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create secure JWT access token with JTI for blacklisting"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    # Add security claims
    jti = secrets.token_urlsafe(16)  # Unique token ID for blacklisting
    to_encode.update({
        "exp": expire,
        "iat": now,
        "jti": jti,
        "iss": settings.app_name,  # Issuer
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        logger.info(f"Access token created for user: {data.get('sub', 'unknown')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation failed: {e}")
        raise

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token with enhanced security checks"""
    try:
        # Check if token is blacklisted
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in _token_blacklist:
            logger.warning("Attempted use of blacklisted token")
            return None
        
        # Decode and validate token
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": True, "verify_iat": True}
        )
        
        # Validate token data structure
        token_data = TokenData(**payload)
        
        # Additional security checks
        if payload.get('iss') != settings.app_name:
            logger.warning("Token issuer mismatch")
            return None
            
        return payload
        
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None

def blacklist_token(token: str) -> bool:
    """Add token to blacklist (for logout)"""
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        _token_blacklist.add(token_hash)
        logger.info("Token blacklisted successfully")
        return True
    except Exception as e:
        logger.error(f"Token blacklisting failed: {e}")
        return False

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    # Basic international phone number validation
    phone_pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(phone_pattern, phone))

def validate_email(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def sanitize_input(input_str: str, max_length: int = 255) -> str:
    """Sanitize user input to prevent XSS and injection attacks"""
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', input_str)
    
    # Limit length
    sanitized = sanitized[:max_length]
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    return sanitized

def generate_secure_otp() -> str:
    """Generate cryptographically secure OTP"""
    return str(secrets.randbelow(900000) + 100000)  # 6-digit OTP

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage"""
    return hashlib.sha256(data.encode()).hexdigest()