from fastapi import APIRouter, HTTPException
from app.config.firebase import get_firestore_client
from app.config.settings import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    try:
        # Test database connectivity
        db = get_firestore_client()
        db.collection('users').limit(1).get()
        return {
            "status": "healthy",
            "database": "connected",
            "firebase": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.app_version
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")