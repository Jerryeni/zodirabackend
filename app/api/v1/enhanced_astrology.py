"""
Enhanced Astrology API Endpoints for ZODIRA Backend

This module provides API endpoints for:
- Persistent authentication
- Enhanced profile management with charts and predictions
- Marriage compatibility analysis
- AI-powered predictions
"""

from datetime import datetime, date, time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.dependencies import get_current_user
from app.config.firebase import get_firestore_client
from app.models.profile import (
    ProfileWithChart, Prediction, PredictionType, MarriageMatch,
    PartnerProfile, Gender
)
from app.services.user_service import user_service
from app.services.enhanced_astrology_service import enhanced_astrology_service
from app.core.exceptions import ValidationError, NotFoundError
from google.cloud import firestore as gcf
from google.cloud.firestore import FieldFilter
from app.services.chatgpt_service import chatgpt_service
import logging
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Persistent Authentication Endpoints

@router.post("/auth/persistent-login")
async def persistent_login(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Check for persistent session on app startup
    """
    try:
        session_token = credentials.credentials

        # Validate persistent session
        auth_data = await user_service.check_persistent_login(session_token)

        if not auth_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session"
            )

        return {
            "message": "Persistent login successful",
            "user_id": auth_data["user_id"],
            "access_token": auth_data["access_token"],
            "user_data": auth_data["user_data"],
            "next_step": auth_data["next_step"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Persistent login failed: {str(e)}"
        )

@router.post("/auth/logout")
async def logout(
    session_token: str = Query(..., description="Persistent session token"),
    current_user: str = Depends(get_current_user)
):
    """
    Logout user and invalidate all sessions
    """
    try:
        # Invalidate persistent session
        await user_service.invalidate_persistent_session(current_user, session_token)

        return {
            "message": "Logged out successfully",
            "user_id": current_user
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/auth/sessions")
async def get_user_sessions(current_user: str = Depends(get_current_user)):
    """
    Get all active sessions for the current user
    """
    try:
        logger.info(f"🔍 Getting sessions for authenticated user: {current_user}")

        # Ensure user has permission to view sessions (basic check)
        if not current_user or len(current_user) < 3:
            logger.warning(f"🚫 Invalid user ID for session access: {current_user}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user authorization"
            )

        sessions = await user_service.get_user_sessions(current_user)

        logger.info(f"✅ Found {len(sessions)} active sessions for user: {current_user}")

        return {
            "sessions": sessions,
            "user_id": current_user,
            "count": len(sessions)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get sessions for user {current_user}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )

# Enhanced Profile Endpoints

@router.post("/profiles/{profile_id}/generate-chart")
async def generate_profile_chart(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Generate complete astrology chart with predictions for a profile
    """
    try:
        # Get profile data (stored in top-level 'person_profiles')
        db = get_firestore_client()
        profile_ref = db.collection('person_profiles').document(profile_id)
        profile_doc = profile_ref.get()

        if not profile_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        profile_data = profile_doc.to_dict()
        # Verify ownership
        if profile_data.get('user_id') != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Generate complete chart with predictions
        enhanced_profile = await enhanced_astrology_service.generate_complete_profile_chart(
            current_user, profile_id, profile_data
        )

        return {
            "message": "Chart generated successfully",
            "profile": enhanced_profile
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chart: {str(e)}"
        )

@router.get("/profiles/{profile_id}/complete")
async def get_complete_profile(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get complete profile with chart, predictions, and marriage matches
    """
    try:
        enhanced_profile = await enhanced_astrology_service.get_profile_with_predictions(
            current_user, profile_id
        )

        if not enhanced_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        return {"profile": enhanced_profile}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )

@router.get("/profiles/{profile_id}/predictions")
async def get_profile_predictions(
    profile_id: str,
    prediction_type: Optional[PredictionType] = None,
    current_user: str = Depends(get_current_user)
):
    """
    Get predictions for a specific profile
    """
    try:
        # Get complete profile to access predictions
        enhanced_profile = await enhanced_astrology_service.get_profile_with_predictions(
            current_user, profile_id
        )

        if not enhanced_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        predictions = enhanced_profile.predictions

        # Filter by prediction type if specified
        if prediction_type:
            predictions = [p for p in predictions if p.prediction_type == prediction_type]

        return {
            "profile_id": profile_id,
            "predictions": predictions,
            "count": len(predictions)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get predictions: {str(e)}"
        )

@router.post("/profiles/{profile_id}/predictions/{prediction_type}")
async def generate_specific_prediction(
    profile_id: str,
    prediction_type: PredictionType,
    current_user: str = Depends(get_current_user)
):
    """
    Generate a specific type of prediction for a profile
    """
    try:
        # Get profile data (stored in top-level 'person_profiles')
        db = get_firestore_client()
        profile_ref = db.collection('person_profiles').document(profile_id)
        profile_doc = profile_ref.get()

        if not profile_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        profile_data = profile_doc.to_dict()

        # Get or generate chart data
        chart_data = await enhanced_astrology_service._generate_astrology_chart(
            current_user, profile_id, profile_data
        )

        # Generate specific prediction
        from app.services.chatgpt_service import chatgpt_service
        prediction_text = await chatgpt_service.generate_personal_predictions(
            profile_data, chart_data, prediction_type.value
        )

        # Calculate expiration
        expires_at = None
        if prediction_type == PredictionType.DAILY:
            from dateutil.relativedelta import relativedelta
            expires_at = datetime.utcnow() + relativedelta(days=1)

        # Create prediction object
        prediction = Prediction(
            id=f"{profile_id}_{prediction_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            profile_id=profile_id,
            user_id=current_user,
            prediction_type=prediction_type,
            prediction_text=prediction_text,
            generated_by="chatgpt",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=expires_at
        )

        # Save to database
        pred_ref = db.collection('predictions').document(prediction.id)
        pred_ref.set(prediction.dict())

        return {
            "message": f"{prediction_type.value.title()} prediction generated successfully",
            "prediction": prediction
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate prediction: {str(e)}"
        )

# Marriage Matching Endpoints

# Request models for marriage matching (prevents 422 by defining explicit body schema)
class PartnerData(BaseModel):
    name: str
    birth_date: date  # Accepts ISO "YYYY-MM-DD"
    birth_time: time  # Accepts ISO "HH:MM:SS"
    birth_place: str
    gender: Gender
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class MarriageMatchRequest(BaseModel):
    main_profile_id: str
    partner_data: PartnerData

@router.post("/marriage-matching/generate")
async def generate_marriage_match(
    request: MarriageMatchRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Generate marriage compatibility analysis between main profile and partner.

    Body JSON (example):
    {
      "main_profile_id": "MAIN_PROFILE_ID",
      "partner_data": {
        "name": "Partner Name",
        "birth_date": "1995-03-15",
        "birth_time": "10:30:00",
        "birth_place": "Mumbai, India",
        "gender": "female",
        "latitude": 19.0760,
        "longitude": 72.8777
      }
    }
    """
    try:
        partner_payload: Dict[str, Any] = request.partner_data.model_dump()
        # Generate marriage match
        marriage_match = await enhanced_astrology_service.generate_marriage_match(
            current_user, request.main_profile_id, partner_payload
        )

        return {
            "message": "Marriage compatibility analysis generated successfully",
            "marriage_match": marriage_match
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate marriage match: {str(e)}"
        )

@router.get("/marriage-matching/{match_id}")
async def get_marriage_match(
    match_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get marriage compatibility analysis by ID
    """
    try:
        db = get_firestore_client()
        match_ref = db.collection('marriage_matches').document(match_id)
        match_doc = match_ref.get()

        if not match_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Marriage match {match_id} not found"
            )

        match_data = match_doc.to_dict()

        # Verify ownership
        if match_data.get('user_id') != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        marriage_match = MarriageMatch(**match_data)

        # Get partner profile details
        partner_ref = db.collection('users').document(current_user).collection('partner_profiles').document(marriage_match.partner_profile_id)
        partner_doc = partner_ref.get()

        partner_profile = None
        if partner_doc.exists:
            partner_profile = PartnerProfile(**partner_doc.to_dict())

        return {
            "marriage_match": marriage_match,
            "partner_profile": partner_profile
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get marriage match: {str(e)}"
        )

@router.get("/profiles/{profile_id}/marriage-matches")
async def get_profile_marriage_matches(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get all marriage matches for a profile
    """
    try:
        db = get_firestore_client()
        matches_ref = db.collection('marriage_matches')
        query = matches_ref.where('main_profile_id', '==', profile_id)\
                          .where('user_id', '==', current_user)\
                          .where('is_active', '==', True)

        matches = []
        for doc in query.stream():
            match_data = doc.to_dict()
            marriage_match = MarriageMatch(**match_data)
            matches.append(marriage_match)

        return {
            "profile_id": profile_id,
            "marriage_matches": matches,
            "count": len(matches)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get marriage matches: {str(e)}"
        )

# Dashboard Endpoints

@router.get("/dashboard")
async def get_dashboard_data(current_user: str = Depends(get_current_user)):
    """
    Get comprehensive dashboard data for the user
    """
    try:
        db = get_firestore_client()

        # Get user profiles from top-level 'person_profiles'
        profiles_query = db.collection('person_profiles')\
            .where(filter=FieldFilter('user_id', '==', current_user))\
            .where(filter=FieldFilter('is_active', '==', True))\
            .limit(5)
        profiles = []

        for doc in profiles_query.get():
            try:
                profile_data = doc.to_dict()
                profile_id = doc.id

                # Get enhanced profile data
                enhanced_profile = await enhanced_astrology_service.get_profile_with_predictions(
                    current_user, profile_id
                )
                if enhanced_profile:
                    profiles.append(enhanced_profile)
            except Exception:
                # Skip problematic profile rather than failing entire dashboard
                continue

        # Get recent predictions
        predictions_ref = db.collection('predictions')
        try:
            recent_predictions_query = predictions_ref.where(filter=FieldFilter('user_id', '==', current_user))\
                                                     .where(filter=FieldFilter('is_active', '==', True))\
                                                     .order_by('created_at', direction=gcf.Query.DESCENDING)\
                                                     .limit(10)
            recent_predictions_docs = list(recent_predictions_query.stream())
        except Exception as e:
            logger.warning(f"Firestore index missing for predictions ordered query; falling back without order: {e}")
            recent_predictions_query = predictions_ref.where(filter=FieldFilter('user_id', '==', current_user))\
                                                     .where(filter=FieldFilter('is_active', '==', True))\
                                                     .limit(10)
            recent_predictions_docs = list(recent_predictions_query.stream())

        recent_predictions = []
        for doc in recent_predictions_docs:
            try:
                pred_data = doc.to_dict()
                prediction = Prediction(**pred_data)
                recent_predictions.append(prediction)
            except Exception as e:
                logger.warning(f"Skipping invalid prediction doc {doc.id}: {e}")

        # Get recent marriage matches
        matches_ref = db.collection('marriage_matches')
        try:
            recent_matches_query = matches_ref.where(filter=FieldFilter('user_id', '==', current_user))\
                                              .where(filter=FieldFilter('is_active', '==', True))\
                                              .order_by('created_at', direction=gcf.Query.DESCENDING)\
                                              .limit(5)
            recent_matches_docs = list(recent_matches_query.stream())
        except Exception as e:
            logger.warning(f"Firestore index missing for matches ordered query; falling back without order: {e}")
            recent_matches_query = matches_ref.where(filter=FieldFilter('user_id', '==', current_user))\
                                              .where(filter=FieldFilter('is_active', '==', True))\
                                              .limit(5)
            recent_matches_docs = list(recent_matches_query.stream())

        recent_matches = []
        for doc in recent_matches_docs:
            try:
                match_data = doc.to_dict()
                marriage_match = MarriageMatch(**match_data)
                recent_matches.append(marriage_match)
            except Exception as e:
                logger.warning(f"Skipping invalid marriage_match doc {doc.id}: {e}")

        return {
            "user_id": current_user,
            "profiles": profiles,
            "recent_predictions": recent_predictions,
            "recent_marriage_matches": recent_matches,
            "summary": {
                "total_profiles": len(profiles),
                "total_predictions": len(recent_predictions),
                "total_marriage_matches": len(recent_matches)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

@router.post("/profiles/{profile_id}/refresh-predictions")
async def refresh_profile_predictions(
    profile_id: str,
    prediction_types: List[PredictionType] = Query(default=[PredictionType.DAILY]),
    current_user: str = Depends(get_current_user)
):
    """
    Refresh/regenerate predictions for a profile
    """
    try:
        # Get profile data (stored in top-level 'person_profiles')
        db = get_firestore_client()
        profile_ref = db.collection('person_profiles').document(profile_id)
        profile_doc = profile_ref.get()

        if not profile_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {profile_id} not found"
            )

        profile_data = profile_doc.to_dict()

        # Generate chart data
        chart_data = await enhanced_astrology_service._generate_astrology_chart(
            current_user, profile_id, profile_data
        )

        # Generate new predictions
        new_predictions = []
        for pred_type in prediction_types:
            prediction_text = await chatgpt_service.generate_personal_predictions(
                profile_data, chart_data, pred_type.value
            )

            # Calculate expiration
            expires_at = None
            if pred_type == PredictionType.DAILY:
                from dateutil.relativedelta import relativedelta
                expires_at = datetime.utcnow() + relativedelta(days=1)

            prediction = Prediction(
                id=f"{profile_id}_{pred_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                profile_id=profile_id,
                user_id=current_user,
                prediction_type=pred_type,
                prediction_text=prediction_text,
                generated_by="chatgpt",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=expires_at
            )

            new_predictions.append(prediction)

        # Save new predictions
        await enhanced_astrology_service._save_predictions_to_db(current_user, profile_id, new_predictions)

        return {
            "message": f"Generated {len(new_predictions)} new predictions",
            "predictions": new_predictions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh predictions: {str(e)}"
        )