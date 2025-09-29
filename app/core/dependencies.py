from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from app.config.firebase import get_firestore_client
import logging

security = HTTPBearer()
logger = logging.getLogger(__name__)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    try:
        token = credentials.credentials
        logger.info(f"🔍 DEBUG: Processing token: {token[:20]}...")
        if not token:
            logger.warning("No token provided in Authorization header.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = verify_token(token)
        logger.info(f"🔍 DEBUG: Token verification result: {payload is not None}")
        if payload is None:
            logger.warning("Token verification failed. Invalid or expired token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = payload.get("sub")
        logger.info(f"🔍 DEBUG: Extracted user_id from token: '{user_id}'")
        logger.info(f"🔍 DEBUG: Full token payload: {payload}")
        if user_id is None:
            logger.error("Token payload is missing 'sub' (subject) claim.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"✅ User {user_id} authenticated successfully")
        return user_id
    except HTTPException as e:
        # Re-raise HTTPException to preserve status code and details
        logger.error(f"🔍 DEBUG: HTTPException in get_current_user: {e.status_code} - {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_firestore_db():
    """Dependency to get Firestore client"""
    return get_firestore_client()

def get_settings():
    """Dependency to get application settings"""
    from app.config.settings import settings
    return settings