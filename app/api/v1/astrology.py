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
from app.models.astrology import AstrologyChartResponse, HouseData, PlanetData, DashaPeriod
from app.config.firebase import get_firestore_client
from app.utils.astrology_utils import calculate_coordinates

logger = logging.getLogger(__name__)

router = APIRouter()

def _build_chart_response_model(chart, user_id: str, profile_id: str) -> AstrologyChartResponse:
    # Coerce datetimes
    _created_at = getattr(chart, 'created_at', None)
    _updated_at = getattr(chart, 'updated_at', None)
    if isinstance(_created_at, str):
        try:
            _created_at = datetime.fromisoformat(_created_at.replace('Z', '+00:00'))
        except Exception:
            _created_at = datetime.utcnow()
    if isinstance(_updated_at, str):
        try:
            _updated_at = datetime.fromisoformat(_updated_at.replace('Z', '+00:00'))
        except Exception:
            _updated_at = _created_at or datetime.utcnow()

    # Coerce houses -> HouseData with PlanetData arrays
    houses_in = getattr(chart, 'houses', {}) or {}
    houses: Dict[str, HouseData] = {}

    def _fnum(v):
        try:
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str) and v.strip() != '':
                return float(v)
        except Exception:
            return None
        return None

    def _fint(v):
        try:
            if v is None or v == '':
                return None
            return int(v)
        except Exception:
            return None

    for i in range(1, 13):
        key = f"house_{i}"
        raw_house = houses_in.get(key, {})
        if isinstance(raw_house, HouseData):
            houses[key] = raw_house
            continue

        planets_list = []
        if isinstance(raw_house, dict):
            raw_planets = raw_house.get('planets', [])
        else:
            raw_planets = []

        for p in raw_planets or []:
            if isinstance(p, PlanetData):
                planets_list.append(p)
            elif isinstance(p, dict):
                planets_list.append(PlanetData(
                    name=str(p.get('name') or p.get('planet') or ''),
                    sign=p.get('sign') or p.get('current_sign'),
                    degree=_fnum(p.get('degree') or p.get('fullDegree') or p.get('full_degree')),
                    strength=_fnum(p.get('strength')),
                    house_number=_fint(p.get('house_number') or p.get('house')),
                    current_sign=p.get('current_sign'),
                    fullDegree=_fnum(p.get('fullDegree') or p.get('full_degree') or p.get('degree')),
                ))
        houses[key] = HouseData(planets=planets_list)

    # General sanitizer for nested values (BaseModel, datetime, lists, dicts)
    def _sanitize(obj):
        try:
            from pydantic import BaseModel as _PBM
        except Exception:
            _PBM = None
        if isinstance(obj, datetime):
            return obj.isoformat()
        if _PBM is not None and isinstance(obj, _PBM):
            try:
                return obj.model_dump()
            except Exception:
                try:
                    return obj.dict()
                except Exception:
                    return str(obj)
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    birth_details = _sanitize(getattr(chart, 'birth_details', {}) or {})
    safe_career = _sanitize(getattr(chart, 'career', {}) or {})
    safe_finance = _sanitize(getattr(chart, 'finance', {}) or {})
    safe_health = _sanitize(getattr(chart, 'health', {}) or {})
    safe_travel = _sanitize(getattr(chart, 'travel', {}) or {})
    safe_vd = _sanitize(getattr(chart, 'vimshottari_dasha', []) or [])

    return AstrologyChartResponse(
        id=f"{user_id}_{profile_id}",
        user_id=user_id,
        profile_id=profile_id,
        houses=houses,
        career=safe_career,
        finance=safe_finance,
        health=safe_health,
        travel=safe_travel,
        vimshottari_dasha=safe_vd,
        birth_details=birth_details,
        created_at=_created_at or datetime.utcnow(),
        updated_at=_updated_at or datetime.utcnow(),
    )

def _build_chart_response_model(chart, user_id: str, profile_id: str) -> AstrologyChartResponse:
    # Coerce datetimes
    _created_at = getattr(chart, 'created_at', None)
    _updated_at = getattr(chart, 'updated_at', None)
    if isinstance(_created_at, str):
        try:
            _created_at = datetime.fromisoformat(_created_at.replace('Z', '+00:00'))
        except Exception:
            _created_at = datetime.utcnow()
    if isinstance(_updated_at, str):
        try:
            _updated_at = datetime.fromisoformat(_updated_at.replace('Z', '+00:00'))
        except Exception:
            _updated_at = _created_at or datetime.utcnow()

    # Coerce houses -> HouseData with PlanetData arrays
    houses_in = getattr(chart, 'houses', {}) or {}
    houses: Dict[str, HouseData] = {}

    def _fnum(v):
        try:
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str) and v.strip() != '':
                return float(v)
        except Exception:
            return None
        return None

    def _fint(v):
        try:
            if v is None or v == '':
                return None
            return int(v)
        except Exception:
            return None

    for i in range(1, 13):
        key = f"house_{i}"
        raw_house = houses_in.get(key, {})
        if isinstance(raw_house, HouseData):
            houses[key] = raw_house
            continue

        planets_list = []
        raw_planets = []
        if isinstance(raw_house, dict):
            raw_planets = raw_house.get('planets', []) or []

        for p in raw_planets:
            if isinstance(p, PlanetData):
                planets_list.append(p)
            elif isinstance(p, dict):
                planets_list.append(PlanetData(
                    name=str(p.get('name') or p.get('planet') or ''),
                    sign=p.get('sign') or p.get('current_sign'),
                    degree=_fnum(p.get('degree') or p.get('fullDegree') or p.get('full_degree')),
                    strength=_fnum(p.get('strength')),
                    house_number=_fint(p.get('house_number') or p.get('house')),
                    current_sign=p.get('current_sign'),
                    fullDegree=_fnum(p.get('fullDegree') or p.get('full_degree') or p.get('degree')),
                ))
        houses[key] = HouseData(planets=planets_list)

    # General sanitizer for nested values (BaseModel, datetime, lists, dicts)
    def _sanitize(obj):
        try:
            from pydantic import BaseModel as _PBM
        except Exception:
            _PBM = None
        if isinstance(obj, datetime):
            return obj.isoformat()
        if _PBM is not None and isinstance(obj, _PBM):
            try:
                return obj.model_dump()
            except Exception:
                try:
                    return obj.dict()
                except Exception:
                    return str(obj)
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    birth_details = _sanitize(getattr(chart, 'birth_details', {}) or {})
    safe_career = _sanitize(getattr(chart, 'career', {}) or {})
    safe_finance = _sanitize(getattr(chart, 'finance', {}) or {})
    safe_health = _sanitize(getattr(chart, 'health', {}) or {})
    safe_travel = _sanitize(getattr(chart, 'travel', {}) or {})

    # Coerce vimshottari_dasha items into DashaPeriod or sanitized dicts
    vd_raw = getattr(chart, 'vimshottari_dasha', []) or []
    vd_list = []
    for item in vd_raw:
        if isinstance(item, DashaPeriod):
            vd_list.append(item)
        elif isinstance(item, dict):
            try:
                # Ensure numeric fields are proper floats
                item_coerced = {
                    'planet': str(item.get('planet', '')),
                    'start_date': str(item.get('start_date', '')),
                    'end_date': str(item.get('end_date', '')),
                    'start_age': float(item.get('start_age')) if item.get('start_age') is not None else 0.0,
                    'end_age': float(item.get('end_age')) if item.get('end_age') is not None else 0.0,
                }
                vd_list.append(DashaPeriod(**item_coerced))
            except Exception:
                # Fallback to sanitized dict; Pydantic will attempt parsing
                vd_list.append(_sanitize(item))
        else:
            vd_list.append(_sanitize(item))

    return AstrologyChartResponse(
        id=f"{user_id}_{profile_id}",
        user_id=user_id,
        profile_id=profile_id,
        houses=houses,
        career=safe_career,
        finance=safe_finance,
        health=safe_health,
        travel=safe_travel,
        vimshottari_dasha=vd_list,
        birth_details=birth_details,
        created_at=_created_at or datetime.utcnow(),
        updated_at=_updated_at or datetime.utcnow(),
    )

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
        # Normalize birth_date/time which may be stored as strings in Firestore
        bd = profile_data.get('birth_date')
        bt = profile_data.get('birth_time')

        if isinstance(bd, str):
            try:
                bd = date.fromisoformat(bd)
            except Exception:
                bd = date.today()

        if isinstance(bt, str):
            try:
                s = bt.strip()
                if s and s.count(':') == 1:
                    s = f"{s}:00"
                bt = time.fromisoformat(s)
            except Exception:
                bt = time(12, 0)

        # Resolve latitude/longitude from birth_place if missing
        latitude = profile_data.get('latitude')
        longitude = profile_data.get('longitude')
        if latitude is None or longitude is None:
            latlng = calculate_coordinates(profile_data.get('birth_place', '') or '')
            latitude = latlng[0] if latlng and len(latlng) == 2 else 20.5937
            longitude = latlng[1] if latlng and len(latlng) == 2 else 78.9629

        birth_details = {
            "year": bd.year,
            "month": bd.month,
            "date": bd.day,
            "hours": bt.hour,
            "minutes": bt.minute,
            "seconds": getattr(bt, 'second', 0) if hasattr(bt, 'second') else 0,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": profile_data.get('timezone', "Asia/Kolkata"),
            "birth_datetime": datetime.combine(bd, bt)
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

        # Convert to response format (coerce created_at/updated_at to datetime if strings)
        _created_at = chart.created_at
        _updated_at = chart.updated_at
        if isinstance(_created_at, str):
            try:
                _created_at = datetime.fromisoformat(_created_at.replace('Z', '+00:00'))
            except Exception:
                _created_at = datetime.utcnow()
        if isinstance(_updated_at, str):
            try:
                _updated_at = datetime.fromisoformat(_updated_at.replace('Z', '+00:00'))
            except Exception:
                _updated_at = _created_at

        chart_response = _build_chart_response_model(chart, current_user, profile_id)

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

# --- Generation endpoints for individual and all chart parts ---

from typing import Literal

@router.post("/profiles/{profile_id}/charts/{chart_type}/generate")
async def generate_chart_part_endpoint(
    profile_id: str,
    chart_type: Literal["rasi", "navamsa", "d10", "chandra", "shadbala"],
    current_user: str = Depends(get_current_user)
):
    """
    Generate a single chart part (rasi, navamsa, d10, chandra, shadbala) for the given profile.
    - Validates ownership
    - Auto-resolves latitude/longitude from birth_place if missing
    - Persists the generated part into astrology_chart_parts
    """
    try:
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(profile_id).get()
        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile_data = profile_doc.to_dict()
        if profile_data.get('user_id') != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        # Normalize birth date/time (strings allowed)
        bd = profile_data.get('birth_date')
        bt = profile_data.get('birth_time')
        if isinstance(bd, str):
            try:
                bd = date.fromisoformat(bd)
            except Exception:
                bd = date.today()
        if isinstance(bt, str):
            try:
                s = bt.strip()
                if s and s.count(':') == 1:
                    s = f"{s}:00"
                bt = time.fromisoformat(s)
            except Exception:
                bt = time(12, 0)

        # Compute lat/lng from birth_place if missing
        latitude = profile_data.get('latitude')
        longitude = profile_data.get('longitude')
        if latitude is None or longitude is None:
            latlng = calculate_coordinates(profile_data.get('birth_place', '') or '')
            latitude = latlng[0] if latlng and len(latlng) == 2 else 20.5937
            longitude = latlng[1] if latlng and len(latlng) == 2 else 78.9629

        birth_details = {
            "year": bd.year,
            "month": bd.month,
            "date": bd.day,
            "hours": bt.hour,
            "minutes": bt.minute,
            "seconds": getattr(bt, 'second', 0) if hasattr(bt, 'second') else 0,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": profile_data.get('timezone', "Asia/Kolkata"),
            "birth_datetime": datetime.combine(bd, bt)
        }

        data = await astrology_service.generate_chart_part(current_user, profile_id, birth_details, chart_type)
        if data is None:
            raise HTTPException(status_code=502, detail=f"Failed to generate {chart_type} chart")
        return {
            "profile_id": profile_id,
            "chart_type": chart_type,
            "status": "generated",
            "message": f"{chart_type} chart generated and stored"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate {chart_type} for {current_user}_{profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate {chart_type} chart")


@router.post("/profiles/{profile_id}/charts/generate-all")
async def generate_all_chart_parts_endpoint(
    profile_id: str,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """
    Generate all chart parts and combined chart for a profile.
    This explicitly triggers background generation and ensures lat/lng are auto-derived
    from birth_place when missing.
    """
    try:
        db = get_firestore_client()
        profile_doc = db.collection('person_profiles').document(profile_id).get()
        if not profile_doc.exists:
            raise HTTPException(status_code=404, detail="Profile not found")
        profile_data = profile_doc.to_dict()
        if profile_data.get('user_id') != current_user:
            raise HTTPException(status_code=403, detail="Not authorized to access this profile")

        bd = profile_data.get('birth_date')
        bt = profile_data.get('birth_time')
        if isinstance(bd, str):
            try:
                bd = date.fromisoformat(bd)
            except Exception:
                bd = date.today()
        if isinstance(bt, str):
            try:
                s = bt.strip()
                if s and s.count(':') == 1:
                    s = f"{s}:00"
                bt = time.fromisoformat(s)
            except Exception:
                bt = time(12, 0)

        # Auto coordinates from birth_place if needed
        latitude = profile_data.get('latitude')
        longitude = profile_data.get('longitude')
        if latitude is None or longitude is None:
            latlng = calculate_coordinates(profile_data.get('birth_place', '') or '')
            latitude = latlng[0] if latlng and len(latlng) == 2 else 20.5937
            longitude = latlng[1] if latlng and len(latlng) == 2 else 78.9629

        birth_details = {
            "year": bd.year,
            "month": bd.month,
            "date": bd.day,
            "hours": bt.hour,
            "minutes": bt.minute,
            "seconds": getattr(bt, 'second', 0) if hasattr(bt, 'second') else 0,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": profile_data.get('timezone', "Asia/Kolkata"),
            "birth_datetime": datetime.combine(bd, bt)
        }

        background_tasks.add_task(
            astrology_service.generate_astrology_chart,
            current_user,
            profile_id,
            birth_details
        )
        return {"status": "processing", "message": "Chart generation started"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start generate-all for {current_user}_{profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start chart generation")

# --- Dashboard extras endpoints ---

@router.post("/profiles/{profile_id}/dashboard-extras/generate")
async def generate_dashboard_extras(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Fetch and persist dashboard extras for a profile:
    - planets_extended: planet name, position, sign, sign lord, house,
      nakshatra number/name/pada, nakshatra vimsottari lord, retrograde
    - vimsottari: maha-dasas and antar-dasas

    Stored under collection 'astrology_dashboard_extras' with doc id '{user_id}_{profile_id}'.
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

        # Normalize birth date/time
        bd = profile_data.get('birth_date')
        bt = profile_data.get('birth_time')
        if isinstance(bd, str):
            try:
                bd = date.fromisoformat(bd)
            except Exception:
                bd = date.today()
        if isinstance(bt, str):
            try:
                s = bt.strip()
                if s and s.count(':') == 1:
                    s = f"{s}:00"
                bt = time.fromisoformat(s)
            except Exception:
                bt = time(12, 0)

        # Resolve latitude/longitude from birth_place if missing
        latitude = profile_data.get('latitude')
        longitude = profile_data.get('longitude')
        if latitude is None or longitude is None:
            latlng = calculate_coordinates(profile_data.get('birth_place', '') or '')
            latitude = latlng[0] if latlng and len(latlng) == 2 else 20.5937
            longitude = latlng[1] if latlng and len(latlng) == 2 else 78.9629

        birth_details = {
            "year": bd.year,
            "month": bd.month,
            "date": bd.day,
            "hours": bt.hour,
            "minutes": bt.minute,
            "seconds": getattr(bt, 'second', 0) if hasattr(bt, 'second') else 0,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": profile_data.get('timezone', "Asia/Kolkata"),
            "birth_datetime": datetime.combine(bd, bt)
        }

        # Fetch upstream data via service
        planets_extended = await astrology_service.fetch_planets_extended(birth_details)
        vimsottari = await astrology_service.fetch_vimsottari(birth_details)

        saved = await astrology_service.save_dashboard_extras(
            current_user, profile_id, planets_extended, vimsottari
        )
        if not saved:
            raise HTTPException(status_code=502, detail="Failed to save dashboard extras")

        return {
            "status": "generated",
            "profile_id": profile_id,
            "has_planets_extended": planets_extended is not None,
            "has_vimsottari": vimsottari is not None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate dashboard extras for user {current_user}, profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard extras")


@router.get("/profiles/{profile_id}/dashboard-extras")
async def get_dashboard_extras(
    profile_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve persisted dashboard extras for a profile.
    Returns 404 if not generated yet.
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

        extras = await astrology_service.get_dashboard_extras(current_user, profile_id)
        if not extras:
            raise HTTPException(status_code=404, detail="Dashboard extras not found. Generate first.")
        return {
            "status": "success",
            "profile_id": profile_id,
            "extras": extras
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard extras for user {current_user}, profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard extras")

# --- Per-part and combined chart retrieval endpoints ---

# Place the 'combined' route BEFORE the dynamic '{chart_type}' route to avoid 422 from Literal mismatch
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

        chart_response = _build_chart_response_model(chart, current_user, profile_id)
        return {"chart": chart_response, "status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve combined chart for user {current_user}, profile {profile_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve combined chart")


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
        # Treat empty dict/list as valid response; only None means missing
        if part is None:
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
