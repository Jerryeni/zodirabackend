from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class PlanetData(BaseModel):
    """Model for individual planet data"""
    name: str
    sign: Optional[str] = None
    degree: Optional[float] = None
    strength: Optional[float] = None
    house_number: Optional[int] = None
    current_sign: Optional[str] = None
    fullDegree: Optional[float] = None

class HouseData(BaseModel):
    """Model for house containing planets"""
    planets: List[PlanetData] = Field(default_factory=list)

class DashaPeriod(BaseModel):
    """Model for Vimshottari Dasha period"""
    planet: str
    start_date: str
    end_date: str
    start_age: float
    end_age: float

class AstrologyChart(BaseModel):
    """Model for complete astrology chart data"""
    user_id: str
    profile_id: str

    # Chart data
    houses: Dict[str, HouseData] = Field(default_factory=lambda: {f"house_{i}": HouseData() for i in range(1, 13)})
    career: Dict[str, Any] = Field(default_factory=dict)
    finance: Dict[str, Any] = Field(default_factory=dict)
    health: Dict[str, Any] = Field(default_factory=dict)
    travel: Dict[str, Any] = Field(default_factory=dict)

    # Dasha data
    vimshottari_dasha: List[DashaPeriod] = Field(default_factory=list)

    # Metadata
    birth_details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AstrologyChartResponse(BaseModel):
    """Response model for astrology chart data"""
    id: str
    user_id: str
    profile_id: str
    houses: Dict[str, HouseData]
    career: Dict[str, Any]
    finance: Dict[str, Any]
    health: Dict[str, Any]
    travel: Dict[str, Any]
    vimshottari_dasha: List[DashaPeriod]
    birth_details: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ChartType(str, Enum):
    """Types of astrology charts"""
    RASI = "rasi"
    NAVAMSA = "navamsa"
    D10 = "d10"
    CHANDRA = "chandra"
    SHADBALA = "shadbala"