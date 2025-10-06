"""
Astrology API Endpoints

This module provides endpoints for astrology chart generation and retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import logging
from datetime import datetime, date, time

from app.services.astrology_service import astrology_service
from app.core.dependencies import get_current_user
from app.models.astrology import AstrologyChartResponse
from app.config.firebase import get_firestore_client

logger = logging.getLogger(__name__)

router = APIRouter()

# Request Models
class GenerateChartRequest(BaseModel):
    """Request model for generating astrology chart"""
    profile_id: str

    @validator('profile_id')
    def validate_profile_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Profile ID cannot be empty')
        return v.strip()

class BirthDetailsRequest(BaseModel):
    """Request model for birth details"""
    year: int
    month: int
    date: int
    hours: int
    minutes: int
    seconds: int
    latitude: float
    longitude: float
    timezone: float

    @validator('year')
    def validate_year(cls, v):
        if not 1900 <= v <= datetime.now().year:
            raise ValueError('Year must be between 1900 and current year')
        return v

    @validator('month')
    def validate_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Month must be between 1 and 12')
        return v

    @validator('date')
    def validate_date(cls, v):
        if not 1 <= v <= 31:
            raise ValueError('Date must be between 1 and 31')
        return v

    @validator('hours')
    def validate_hours(cls, v):
        if not 0 <= v <= 23:
            raise ValueError('Hours must be between 0 and 23')
        return v

    @validator('minutes', 'seconds')
    def validate_minutes_seconds(cls, v):
        if not 0 <= v <= 59:
            raise ValueError('Minutes/Seconds must be between 0 and 59')
        return v

    @validator('latitude')
    def validate_latitude(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @validator('timezone')
    def validate_timezone(cls, v):
        if not -12 <= v <= 14:
            raise ValueError('Timezone must be between -12 and 14')
        return v

# Response Models
class GenerateChartResponse(BaseModel):
    """Response model for chart generation"""
    message: str
    chart_id: str
    status: str

class ChartDataResponse(BaseModel):
    """Response model for chart data"""
    chart: AstrologyChartResponse
    status: str

# API Endpoints
@router.post("/generate-chart", response_model=GenerateChartResponse)
async def generate_astrology_chart(
    request: GenerateChartRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    Generate astrology chart for a user profile

    This endpoint:
    1. Validates the profile belongs to the user
    2. Retrieves birth details from the profile
    3. Generates complete astrology chart in background
    4. Returns chart generation status
    """
    try:
        # Validate profile ownership
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(request.profile_id).get()

        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_data = profile_doc.to_dict()
        if profile_data['user_id'] != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        # Check if chart already exists
        chart_id = f"{current_user}_{request.profile_id}"
        existing_chart = await astrology_service.get_astrology_chart(current_user, request.profile_id)
        if existing_chart:
            return GenerateChartResponse(
                message="Chart already exists",
                chart_id=chart_id,
                status="exists"
            )

        # Prepare birth details
        birth_details = {
            "year": profile_data['birth_date'].year,
            "month": profile_data['birth_date'].month,
            "date": profile_data['birth_date'].day,
            "hours": profile_data['birth_time'].hour,
            "minutes": profile_data['birth_time'].minute,
            "seconds": profile_data['birth_time'].second,
            "latitude": profile_data.get('latitude', 20.5937),  # Default to India center
            "longitude": profile_data.get('longitude', 78.9629),
            "timezone": profile_data.get('timezone', 5.5),
            "birth_datetime": datetime.combine(profile_data['birth_date'], profile_data['birth_time'])
        }

        # Generate chart in background
        background_tasks.add_task(
            astrology_service.generate_astrology_chart,
            current_user,
            request.profile_id,
            birth_details
        )

        logger.info(f"Started astrology chart generation for user {current_user}, profile {request.profile_id}")

        return GenerateChartResponse(
            message="Chart generation started",
            chart_id=chart_id,
            status="processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start chart generation for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start chart generation")

@router.get("/chart/{profile_id}", response_model=ChartDataResponse)
async def get_astrology_chart(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve astrology chart for a user profile

    This endpoint:
    1. Validates profile ownership
    2. Retrieves chart data from database
    3. Returns structured chart information
    """
    try:
        # Validate profile ownership
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(profile_id).get()

        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_data = profile_doc.to_dict()
        if profile_data['user_id'] != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        # Get chart data
        chart = await astrology_service.get_astrology_chart(current_user, profile_id)
        if not chart:
            raise HTTPException(status_code=404, detail="Astrology chart not found. Please generate the chart first.")

        # Convert to response format
        chart_response = AstrologyChartResponse(
            id=f"{current_user}_{profile_id}",
            user_id=chart.user_id,
            profile_id=chart.profile_id,
            houses=chart.houses,
            career=chart.career,
            finance=chart.finance,
            health=chart.health,
            travel=chart.travel,
            vimshottari_dasha=chart.vimshottari_dasha,
            birth_details=chart.birth_details,
            created_at=chart.created_at,
            updated_at=chart.updated_at
        )

        return ChartDataResponse(
            chart=chart_response,
            status="success"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve astrology chart for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve astrology chart")

@router.get("/chart/{profile_id}/status")
async def get_chart_generation_status(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Check astrology chart generation status

    This endpoint checks if a chart exists and provides status information
    """
    try:
        # Validate profile ownership
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(profile_id).get()

        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_data = profile_doc.to_dict()
        if profile_data['user_id'] != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        # Check if chart exists
        chart = await astrology_service.get_astrology_chart(current_user, profile_id)
        if chart:
            return {
                "status": "completed",
                "chart_id": f"{current_user}_{profile_id}",
                "created_at": chart.created_at.isoformat(),
                "message": "Chart is ready"
            }
        else:
            return {
                "status": "not_found",
                "chart_id": f"{current_user}_{profile_id}",
                "message": "Chart not found. Please generate the chart first."
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check chart status for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check chart status")

@router.delete("/chart/{profile_id}")
async def delete_astrology_chart(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Delete astrology chart for a user profile

    This endpoint removes the chart data from the database
    """
    try:
        # Validate profile ownership
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(profile_id).get()

        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile_data = profile_doc.to_dict()
        if profile_data['user_id'] != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        # Delete chart
        chart_id = f"{current_user}_{profile_id}"
        doc_ref = db.collection('astrology_charts').document(chart_id)
        doc_ref.delete()

        logger.info(f"Deleted astrology chart {chart_id}")

        return {
            "message": "Chart deleted successfully",
            "chart_id": chart_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete astrology chart for user {current_user}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete astrology chart")

# --- Per-part chart retrieval endpoints (Rasi/Navamsa/D10/Chandra/Shadbala) ---

from typing import Literal

@router.get("/profiles/{profile_id}/charts/{chart_type}")
async def get_chart_part_endpoint(
    profile_id: str,
    chart_type: Literal["rasi", "navamsa", "d10", "chandra", "shadbala"],
    current_user: str = Depends(get_current_user)
):
    """
    Return a single astrology chart part (rasi, navamsa, d10, chandra, shadbala) for the given profile.
    - Validates ownership (profile belongs to the authenticated user)
    - Fetches raw chart part persisted in astrology_chart_parts
    """
    try:
        # Validate profile ownership
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(profile_id).get()
        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")

        data = profile_doc.to_dict()
        if data.get('user_id') != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        # Fetch chart part
        part = await astrology_service.get_chart_part(current_user, profile_id, chart_type)
        if not part:
            raise HTTPException(status_code=404, detail=f"{chart_type} chart not found. Generate the chart first.")

        return {
            "profile_id": profile_id,
            "chart_type": chart_type,
            "data": part,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve {chart_type} chart part for user {current_user}, profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve {chart_type} chart part")


@router.get("/profiles/{profile_id}/charts/combined")
async def get_combined_chart_endpoint(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Alias for combined chart retrieval (same as GET /chart/{profile_id}).
    Returns the structured AstrologyChartResponse.
    """
    try:
        # Validate profile ownership
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(profile_id).get()
        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile_data = profile_doc.to_dict()
        if profile_data.get('user_id') != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        chart = await astrology_service.get_astrology_chart(current_user, profile_id)
        if not chart:
            raise HTTPException(status_code=404, detail="Astrology chart not found. Please generate the chart first.")

        chart_response = AstrologyChartResponse(
            id=f"{current_user}_{profile_id}",
            user_id=chart.user_id,
            profile_id=chart.profile_id,
            houses=chart.houses,
            career=chart.career,
            finance=chart.finance,
            health=chart.health,
            travel=chart.travel,
            vimshottari_dasha=chart.vimshottari_dasha,
            birth_details=chart.birth_details,
            created_at=chart.created_at,
            updated_at=chart.updated_at
        )
        return {"chart": chart_response, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve combined chart for user {current_user}, profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve combined chart")
