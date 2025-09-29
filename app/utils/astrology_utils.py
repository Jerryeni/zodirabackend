"""
Astrology utility functions for ZODIRA
"""

from datetime import date, time
from typing import Tuple, Optional
import math

def calculate_zodiac_sign(birth_date: date) -> str:
    """Calculate zodiac sign from birth date"""
    day = birth_date.day
    month = birth_date.month

    zodiac_signs = [
        "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini",
        "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"
    ]
    zodiac_dates = [20, 19, 21, 20, 21, 21, 23, 23, 23, 23, 22, 22]
    zodiac_index = month - 1 if day >= zodiac_dates[month - 1] else (month - 2) % 12
    return zodiac_signs[zodiac_index]

def calculate_nakshatra(birth_date: date, birth_time: time) -> str:
    """Calculate birth nakshatra from birth date and time"""
    # Simplified calculation - in production, use proper astronomical calculations
    day_of_year = birth_date.timetuple().tm_yday
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

    # Each nakshatra spans approximately 13.33 degrees (360/27)
    nakshatra_index = (day_of_year % 27)
    return nakshatras[nakshatra_index]

def calculate_coordinates(birth_place: str) -> Tuple[Optional[float], Optional[float]]:
    """Calculate latitude and longitude from birth place"""
    # In production, use geocoding service like Google Maps API
    # For demo purposes, return mock coordinates for major cities

    city_coords = {
        "mumbai": (19.0760, 72.8777),
        "delhi": (28.7041, 77.1025),
        "bangalore": (12.9716, 77.5946),
        "chennai": (13.0827, 80.2707),
        "kolkata": (22.5726, 88.3639),
        "ahmedabad": (23.0225, 72.5714),
        "pune": (18.5204, 73.8567),
        "jaipur": (26.9124, 75.7873),
        "lucknow": (26.8467, 80.9462),
        "kanpur": (26.4499, 80.3319)
    }

    place_lower = birth_place.lower().strip()
    for city, coords in city_coords.items():
        if city in place_lower:
            return coords

    # Default coordinates for India
    return (20.5937, 78.9629)

def validate_birth_details(birth_date: date, birth_time: time, birth_place: str) -> bool:
    """Validate birth details for astrology calculations"""
    if not birth_date or not birth_time or not birth_place:
        return False

    # Check if birth date is not in future
    if birth_date > date.today():
        return False

    # Check if birth place is reasonable length
    if len(birth_place.strip()) < 2:
        return False

    return True

def format_astrology_time(birth_time: time) -> str:
    """Format birth time for astrology display"""
    return birth_time.strftime("%I:%M %p")

def get_lucky_numbers(zodiac_sign: str) -> list:
    """Get lucky numbers based on zodiac sign"""
    lucky_numbers_map = {
        "Aries": [1, 8, 17],
        "Taurus": [2, 6, 9, 12, 24],
        "Gemini": [5, 7, 14, 23],
        "Cancer": [2, 7, 11, 16, 20],
        "Leo": [1, 3, 10, 19],
        "Virgo": [3, 8, 13, 18, 23],
        "Libra": [4, 6, 13, 15, 24],
        "Scorpio": [8, 11, 18, 22],
        "Sagittarius": [3, 9, 12, 21],
        "Capricorn": [4, 8, 13, 22],
        "Aquarius": [4, 7, 11, 22, 29],
        "Pisces": [3, 9, 12, 15, 18, 24]
    }

    return lucky_numbers_map.get(zodiac_sign, [7])  # Default lucky number

def get_lucky_colors(zodiac_sign: str) -> list:
    """Get lucky colors based on zodiac sign"""
    lucky_colors_map = {
        "Aries": ["Red", "White"],
        "Taurus": ["Green", "Pink"],
        "Gemini": ["Yellow", "Green"],
        "Cancer": ["White", "Blue"],
        "Leo": ["Gold", "Orange"],
        "Virgo": ["Green", "White"],
        "Libra": ["Blue", "Pink"],
        "Scorpio": ["Red", "Black"],
        "Sagittarius": ["Purple", "Blue"],
        "Capricorn": ["Black", "Brown"],
        "Aquarius": ["Blue", "Silver"],
        "Pisces": ["Sea Green", "White"]
    }

    return lucky_colors_map.get(zodiac_sign, ["Blue"])  # Default color