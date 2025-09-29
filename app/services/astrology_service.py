"""
Astrology Service for ZODIRA Backend

This service handles astrology chart calculations, API integrations,
and data processing for Vedic astrology features.
"""

import os
import json
import time
import logging
from datetime import datetime, date, time
from typing import Dict, List, Optional, Any, Tuple
from dateutil.relativedelta import relativedelta
import requests
import httpx

from app.config.settings import settings
from app.config.firebase import get_firestore_client
from app.config.settings import settings
from app.models.astrology import AstrologyChart, PlanetData, HouseData, DashaPeriod
from app.utils.astrology_utils import calculate_coordinates

logger = logging.getLogger(__name__)

class AstrologyService:
    """Service for handling astrology calculations and API integrations"""

    def __init__(self):
        self.free_astro_api_key = settings.free_astrology_api_key
        self.api_endpoints = {
            "rasi": "https://json.freeastrologyapi.com/planets",
            "navamsa": "https://json.freeastrologyapi.com/navamsa-chart-info",
            "d10": "https://json.freeastrologyapi.com/d10-chart-info",
            "chandra": "https://json.freeastrologyapi.com/chandra-kundali-info",
            "shadbala": "https://json.freeastrologyapi.com/shadbala/summary"
        }
        self._db = None
        self._vimshottari_order = None

    @property
    def db(self):
        """Lazy initialization of Firestore client"""
        if self._db is None:
            self._db = get_firestore_client()
        return self._db

    @property
    def vimshottari_order(self):
        """Get Vimshottari Dasha order from database"""
        if self._vimshottari_order is None:
            self._vimshottari_order = self._get_or_init_vimshottari_order()
        return self._vimshottari_order

    async def generate_astrology_chart(self, user_id: str, profile_id: str, birth_details: Dict[str, Any]) -> AstrologyChart:
        """
        Generate complete astrology chart for a user profile

        Args:
            user_id: User ID
            profile_id: Profile ID
            birth_details: Birth details dictionary

        Returns:
            AstrologyChart: Complete chart data
        """
        try:
            logger.info(f"Generating astrology chart for user {user_id}, profile {profile_id}")

            # Fetch all chart data
            chart_data = await self._fetch_all_charts(birth_details)

            # Calculate Vimshottari Dasha
            moon_longitude = self._extract_moon_longitude(chart_data.get("rasi", {}))
            vimshottari_dasha = self._compute_vimshottari_dasha(
                birth_details["birth_datetime"], moon_longitude
            )

            # Structure the data
            structured_data = self._structure_astrology_data(
                chart_data.get("rasi", {}),
                chart_data.get("navamsa", {}),
                chart_data.get("d10", {}),
                chart_data.get("chandra", {}),
                chart_data.get("shadbala", {})
            )

            # Create chart object
            chart = AstrologyChart(
                user_id=user_id,
                profile_id=profile_id,
                houses=structured_data["houses"],
                career=structured_data["career"],
                finance=structured_data["finance"],
                health=structured_data["health"],
                travel=structured_data["travel"],
                vimshottari_dasha=vimshottari_dasha,
                birth_details=birth_details
            )

            # Save to database
            await self._save_chart_to_db(chart)

            logger.info(f"Successfully generated and saved astrology chart for user {user_id}")
            return chart

        except Exception as e:
            logger.error(f"Failed to generate astrology chart for user {user_id}: {e}")
            raise

    async def get_astrology_chart(self, user_id: str, profile_id: str) -> Optional[AstrologyChart]:
        """
        Retrieve astrology chart from database

        Args:
            user_id: User ID
            profile_id: Profile ID

        Returns:
            AstrologyChart or None if not found
        """
        try:
            doc_ref = self.db.collection('astrology_charts').document(f"{user_id}_{profile_id}")
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                return AstrologyChart(**data)
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve astrology chart for user {user_id}: {e}")
            return None

    async def _fetch_all_charts(self, birth_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch all astrology charts from external API

        Args:
            birth_details: Birth details for API request

        Returns:
            Dict containing all chart data
        """
        charts_data = {}
        cache_dir = "cache/astrology"
        os.makedirs(cache_dir, exist_ok=True)

        for chart_type, url in self.api_endpoints.items():
            cache_file = os.path.join(cache_dir, f"{chart_type}_{birth_details['year']}_{birth_details['month']}_{birth_details['date']}.json")

            try:
                data = await self._fetch_chart_with_cache(url, birth_details, cache_file)
                charts_data[chart_type] = data
                logger.info(f"Successfully fetched {chart_type} chart")
            except Exception as e:
                logger.warning(f"Failed to fetch {chart_type} chart: {e}")
                charts_data[chart_type] = {}

        return charts_data

    async def _fetch_chart_with_cache(self, url: str, details: Dict[str, Any], cache_file: str) -> Dict[str, Any]:
        """
        Fetch chart data with caching mechanism

        Args:
            url: API endpoint URL
            details: Request payload
            cache_file: Cache file path

        Returns:
            Chart data dictionary
        """
        # Check cache first
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    logger.info(f"Loading {cache_file} from cache")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache file {cache_file}: {e}")

        # Fetch from API
        headers = {"x-api-key": self.free_astro_api_key}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=details, headers=headers)

            if response.status_code == 200:
                data = response.json()
                # Cache the result
                try:
                    with open(cache_file, "w") as f:
                        json.dump(data, f)
                    logger.info(f"Cached {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to cache {cache_file}: {e}")

                time.sleep(1)  # Rate limiting
                return data
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded. Please try again later.")
            elif response.status_code == 403:
                raise Exception("Authentication failed. Check API key.")
            elif response.status_code == 404:
                raise Exception(f"Endpoint not found: {url}")
            else:
                raise Exception(f"API Error {response.status_code}: {response.text}")

    def _extract_moon_longitude(self, rasi_data: Dict[str, Any]) -> Optional[float]:
        """
        Extract Moon longitude from Rasi chart data

        Args:
            rasi_data: Rasi chart data

        Returns:
            Moon longitude or None
        """
        try:
            rasi_planets = rasi_data.get("output", [])[0] if rasi_data.get("output") else {}
            for planet_data in rasi_planets.values():
                if planet_data.get("name") == "Moon":
                    return planet_data.get("fullDegree")
            return None
        except Exception as e:
            logger.error(f"Failed to extract Moon longitude: {e}")
            return None

    def _compute_vimshottari_dasha(self, birth_datetime: datetime, moon_longitude: Optional[float]) -> List[DashaPeriod]:
        """
        Compute Vimshottari Dasha periods

        Args:
            birth_datetime: Birth datetime
            moon_longitude: Moon longitude in degrees

        Returns:
            List of DashaPeriod objects
        """
        if moon_longitude is None:
            logger.warning("Moon longitude not available, using default for Dasha calculation")
            moon_longitude = 0

        nakshatra_size = 13.3333333
        nakshatra_index = int(moon_longitude // nakshatra_size)
        lord, full_years = self.vimshottari_order[nakshatra_index]

        nakshatra_start = nakshatra_index * nakshatra_size
        nakshatra_progress = moon_longitude - nakshatra_start
        balance_fraction = (nakshatra_size - nakshatra_progress) / nakshatra_size
        balance_years = full_years * balance_fraction

        dasha_sequence = []
        current_time = birth_datetime

        # First Dasha (partial)
        dasha_end = current_time + relativedelta(years=int(balance_years),
                                                 months=int((balance_years % 1) * 12))
        dasha_sequence.append(DashaPeriod(
            planet=lord,
            start_date=current_time.strftime("%Y-%m-%d"),
            end_date=dasha_end.strftime("%Y-%m-%d"),
            start_age=round((current_time - birth_datetime).days / 365.25, 2),
            end_age=round((dasha_end - birth_datetime).days / 365.25, 2)
        ))
        current_time = dasha_end

        # Remaining Dashas
        order_index = nakshatra_index
        for i in range(1, len(self.vimshottari_order) * 12):
            order_index = (nakshatra_index + i) % len(self.vimshottari_order)
            lord, full_years = self.vimshottari_order[order_index]
            dasha_end = current_time + relativedelta(years=full_years)

            dasha_sequence.append(DashaPeriod(
                planet=lord,
                start_date=current_time.strftime("%Y-%m-%d"),
                end_date=dasha_end.strftime("%Y-%m-%d"),
                start_age=round((current_time - birth_datetime).days / 365.25, 2),
                end_age=round((dasha_end - birth_datetime).days / 365.25, 2)
            ))

            current_time = dasha_end
            if (current_time - birth_datetime).days / 365.25 >= 120:
                break

        return dasha_sequence

    def _structure_astrology_data(self, rasi, navamsa, d10, chandra, shadbala) -> Dict[str, Any]:
        """
        Structure astrology data into organized format

        Args:
            rasi, navamsa, d10, chandra, shadbala: Chart data dictionaries

        Returns:
            Structured astrology data
        """
        structured = {
            "houses": {f"house_{i}": HouseData() for i in range(1, 13)},
            "career": {},
            "finance": {},
            "health": {},
            "travel": {}
        }

        # Process Rasi planets
        if rasi and rasi.get("output"):
            rasi_planets = rasi["output"][0]
            for planet_data in rasi_planets.values():
                house_num = planet_data.get("house_number") or planet_data.get("house")
                if house_num and 1 <= house_num <= 12:
                    planet = PlanetData(
                        name=planet_data.get("name"),
                        sign=planet_data.get("current_sign"),
                        degree=planet_data.get("fullDegree"),
                        strength=shadbala.get("output", {}).get(planet_data.get("name"), {}).get("Shadbala") if shadbala else None,
                        house_number=house_num,
                        current_sign=planet_data.get("current_sign"),
                        fullDegree=planet_data.get("fullDegree")
                    )
                    structured["houses"][f"house_{house_num}"].planets.append(planet)

        # Career data
        structured["career"] = {
            "10th_house_planets": structured["houses"]["house_10"].planets,
            "d10_summary": d10.get("output", {}),
            "strengths": shadbala.get("output", {}) if shadbala else {}
        }

        # Finance data
        structured["finance"] = {
            "2nd_house_planets": structured["houses"]["house_2"].planets,
            "11th_house_planets": structured["houses"]["house_11"].planets,
            "strengths": shadbala.get("output", {}) if shadbala else {}
        }

        # Health data
        structured["health"] = {
            "6th_house_planets": structured["houses"]["house_6"].planets,
            "8th_house_planets": structured["houses"]["house_8"].planets,
            "strengths": shadbala.get("output", {}) if shadbala else {}
        }

        # Travel data
        structured["travel"] = {
            "3rd_house_planets": structured["houses"]["house_3"].planets,
            "12th_house_planets": structured["houses"]["house_12"].planets,
            "strengths": shadbala.get("output", {}) if shadbala else {}
        }

        return structured

    def _get_or_init_vimshottari_order(self):
        """
        Get Vimshottari Dasha order from database, initialize if not exists

        Returns:
            List of tuples: [(planet_name, years), ...]
        """
        try:
            doc_ref = self.db.collection('astrology_config').document('vimshottari_order')
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                return data.get('order', [])
            else:
                # Initialize with default values
                default_order = [
                    ("Ketu", 7),
                    ("Venus", 20),
                    ("Sun", 6),
                    ("Moon", 10),
                    ("Mars", 7),
                    ("Rahu", 18),
                    ("Jupiter", 16),
                    ("Saturn", 19),
                    ("Mercury", 17),
                ]

                doc_ref.set({
                    'order': default_order,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })

                logger.info("Initialized Vimshottari Dasha order in database")
                return default_order

        except Exception as e:
            logger.error(f"Failed to get Vimshottari order from database: {e}")
            # Fallback to hardcoded values
            return [
                ("Ketu", 7),
                ("Venus", 20),
                ("Sun", 6),
                ("Moon", 10),
                ("Mars", 7),
                ("Rahu", 18),
                ("Jupiter", 16),
                ("Saturn", 19),
                ("Mercury", 17),
            ]

    async def _save_chart_to_db(self, chart: AstrologyChart) -> None:
        """
        Save astrology chart to Firestore

        Args:
            chart: AstrologyChart object to save
        """
        try:
            doc_id = f"{chart.user_id}_{chart.profile_id}"
            doc_ref = self.db.collection('astrology_charts').document(doc_id)
            chart.updated_at = datetime.utcnow()
            doc_ref.set(chart.dict())
            logger.info(f"Saved astrology chart {doc_id} to database")
        except Exception as e:
            logger.error(f"Failed to save astrology chart to database: {e}")
            raise

# Global service instance
astrology_service = AstrologyService()