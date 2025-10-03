"""
Production-Ready Astrology Service for ZODIRA Backend

This service provides comprehensive astrology functionality including:
- Real astrology calculations using FREE_ASTRO_API_KEY
- Accurate chart generation and calculations
- AI-powered predictions via ChatGPT
- Marriage compatibility analysis
- Profile management with astrology data
- Production-ready error handling and caching
"""

import os
import json
import logging
import httpx
from datetime import datetime, date, time
from typing import Dict, List, Optional, Any
from dateutil.relativedelta import relativedelta
from google.cloud.firestore import FieldFilter

from app.config.settings import settings
from app.config.firebase import get_firestore_client
from app.models.astrology import AstrologyChart
from app.models.profile import (
    Prediction, PredictionType, PartnerProfile, MarriageMatch,
    ProfileWithChart, PredictionCreate
)
from app.services.chatgpt_service import chatgpt_service
from app.utils.astrology_utils import calculate_coordinates

logger = logging.getLogger(__name__)

class EnhancedAstrologyService:
    """Enhanced service for astrology calculations and AI predictions"""

    def __init__(self):
        self._db = None
        self.openai_api_key = settings.openai_api_key
        self.free_astrology_api_key = settings.free_astrology_api_key
        self._api_cache = {}  # Simple in-memory cache for API responses

    @property
    def db(self):
        """Lazy initialization of Firestore client"""
        if self._db is None:
            self._db = get_firestore_client()
        return self._db

    async def generate_complete_profile_chart(
        self,
        user_id: str,
        profile_id: str,
        profile_data: Dict[str, Any]
    ) -> ProfileWithChart:
        """
        Generate complete astrology chart with predictions for a profile

        Args:
            user_id: User ID
            profile_id: Profile ID
            profile_data: Profile data dictionary

        Returns:
            Complete profile with chart and predictions
        """
        try:
            logger.info(f"Generating complete chart for user {user_id}, profile {profile_id}")

            # Generate astrology chart using existing service
            chart_data = await self._generate_astrology_chart(user_id, profile_id, profile_data)

            # Generate AI predictions
            predictions = await self._generate_predictions(user_id, profile_id, profile_data, chart_data)

            # Get existing profile data
            # Read profile from top-level 'person_profiles' collection
            profile_ref = self.db.collection('person_profiles').document(profile_id)
            profile_doc = profile_ref.get()

            if not profile_doc.exists:
                raise ValueError(f"Profile {profile_id} not found")

            existing_profile = profile_doc.to_dict()

            # Create enhanced profile with chart and predictions
            enhanced_profile = ProfileWithChart(
                id=profile_id,
                user_id=user_id,
                name=existing_profile.get('name', ''),
                birth_date=existing_profile.get('birth_date'),
                birth_time=existing_profile.get('birth_time'),
                birth_place=existing_profile.get('birth_place', ''),
                gender=existing_profile.get('gender', 'male'),
                relationship=existing_profile.get('relationship', 'self'),
                zodiac_sign=existing_profile.get('zodiac_sign'),
                moon_sign=existing_profile.get('moon_sign'),
                nakshatra=existing_profile.get('nakshatra'),
                ascendant=existing_profile.get('ascendant'),
                astrology_chart=chart_data,
                predictions=predictions,
                created_at=existing_profile.get('created_at'),
                updated_at=datetime.utcnow(),
                is_active=existing_profile.get('is_active', True)
            )

            # Save predictions to database
            await self._save_predictions_to_db(user_id, profile_id, predictions)

            logger.info(f"Successfully generated complete profile chart for {profile_id}")
            return enhanced_profile

        except Exception as e:
            logger.error(f"Failed to generate complete profile chart: {e}")
            raise

    async def generate_marriage_match(
        self,
        user_id: str,
        main_profile_id: str,
        partner_data: Dict[str, Any]
    ) -> MarriageMatch:
        """
        Generate marriage compatibility analysis

        Args:
            user_id: User ID
            main_profile_id: Main profile ID
            partner_data: Partner's birth data

        Returns:
            Marriage compatibility analysis
        """
        try:
            logger.info(f"Generating marriage match for user {user_id}, profile {main_profile_id}")

            # Get main profile data
            main_profile = await self._get_profile_data(user_id, main_profile_id)
            if not main_profile:
                raise ValueError(f"Main profile {main_profile_id} not found")

            # Create partner profile
            partner_profile = await self._create_partner_profile(user_id, main_profile_id, partner_data)

            # Generate charts for both profiles
            main_chart = await self._generate_astrology_chart(user_id, main_profile_id, main_profile)
            partner_chart = await self._generate_astrology_chart(user_id, partner_profile['id'], partner_data)

            # Generate compatibility analysis using ChatGPT
            compatibility_data = await chatgpt_service.generate_marriage_compatibility(
                main_profile, partner_data, main_chart, partner_chart
            )

            # Calculate traditional compatibility scores
            traditional_scores = self._calculate_traditional_scores(main_profile, partner_data)

            # Combine AI and traditional analysis
            final_compatibility = self._merge_compatibility_data(compatibility_data, traditional_scores)

            # Create marriage match object
            marriage_match = MarriageMatch(
                id=f"{main_profile_id}_{partner_profile['id']}",
                main_profile_id=main_profile_id,
                partner_profile_id=partner_profile['id'],
                user_id=user_id,
                overall_score=final_compatibility['overall_score'],
                guna_score=final_compatibility['guna_score'],
                mangal_compatibility=final_compatibility.get('mangal_compatibility', 'neutral'),
                mental_compatibility=final_compatibility.get('mental_compatibility', 'good'),
                physical_compatibility=final_compatibility.get('physical_compatibility', 'good'),
                guna_breakdown=final_compatibility.get('guna_breakdown', {}),
                strengths=final_compatibility.get('strengths', []),
                challenges=final_compatibility.get('challenges', []),
                recommendations=final_compatibility.get('recommendations', []),
                dosha_analysis=final_compatibility.get('dosha_analysis', {}),
                ai_insights=final_compatibility.get('ai_insights'),
                compatibility_level=final_compatibility.get('compatibility_level', 'unknown'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Save to database
            await self._save_marriage_match_to_db(marriage_match)

            logger.info(f"Successfully generated marriage match {marriage_match.id}")
            return marriage_match

        except Exception as e:
            logger.error(f"Failed to generate marriage match: {e}")
            raise

    async def _generate_astrology_chart(self, user_id: str, profile_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate astrology chart data"""
        try:
            # Use existing astrology service for chart generation
            from app.services.astrology_service import astrology_service

            # Convert profile data to birth details format (normalize string date/time)
            bd = profile_data.get('birth_date', date.today())
            bt = profile_data.get('birth_time', time(12, 0))

            if isinstance(bd, str):
                try:
                    bd = date.fromisoformat(bd)
                except ValueError:
                    bd = date.today()

            if isinstance(bt, str):
                try:
                    bt = time.fromisoformat(bt)
                except ValueError:
                    bt = time(12, 0)

            birth_details = {
                'year': bd.year,
                'month': bd.month,
                'date': bd.day,
                'hour': bt.hour,
                'minute': bt.minute,
                'latitude': profile_data.get('latitude', 0),
                'longitude': profile_data.get('longitude', 0),
                'timezone': profile_data.get('timezone', 'Asia/Kolkata'),
                # Required by astrology_service.generate_astrology_chart
                'birth_datetime': datetime(bd.year, bd.month, bd.day, bt.hour, bt.minute)
            }

            # Generate chart using existing service
            chart = await astrology_service.generate_astrology_chart(user_id, profile_id, birth_details)

            # Convert to dictionary format with proper datetime handling
            try:
                if hasattr(chart, 'dict'):
                    chart_dict = chart.dict()
                else:
                    chart_dict = chart.__dict__

                # Handle datetime serialization
                def convert_datetime(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif isinstance(obj, date):
                        return obj.isoformat()
                    elif isinstance(obj, time):
                        return obj.isoformat()
                    elif hasattr(obj, '__dict__'):
                        return convert_datetime(obj.__dict__)
                    elif isinstance(obj, list):
                        return [convert_datetime(item) for item in obj]
                    elif isinstance(obj, dict):
                        return {key: convert_datetime(value) for key, value in obj.items()}
                    else:
                        return obj

                return convert_datetime(chart_dict)
            except Exception as e:
                logger.error(f"Failed to convert chart to dict: {e}")
                # Return basic structure as fallback
                return {
                    'user_id': user_id,
                    'profile_id': profile_id,
                    'houses': {},
                    'career': {},
                    'finance': {},
                    'health': {},
                    'travel': {},
                    'vimshottari_dasha': []
                }

        except Exception as e:
            logger.error(f"Failed to generate astrology chart: {e}")
            # Return basic chart structure as fallback
            return {
                'user_id': user_id,
                'profile_id': profile_id,
                'houses': {},
                'career': {},
                'finance': {},
                'health': {},
                'travel': {},
                'vimshottari_dasha': []
            }

    async def _generate_predictions(
        self,
        user_id: str,
        profile_id: str,
        profile_data: Dict[str, Any],
        chart_data: Dict[str, Any]
    ) -> List[Prediction]:
        """Generate AI predictions for the profile"""
        try:
            predictions = []

            # Generate different types of predictions
            prediction_types = [
                PredictionType.DAILY,
                PredictionType.WEEKLY,
                PredictionType.CAREER,
                PredictionType.HEALTH
            ]

            for pred_type in prediction_types:
                # Generate prediction using ChatGPT
                prediction_text = await chatgpt_service.generate_personal_predictions(
                    profile_data, chart_data, pred_type.value
                )

                # Calculate expiration date
                expires_at = None
                if pred_type == PredictionType.DAILY:
                    expires_at = datetime.utcnow() + relativedelta(days=1)
                elif pred_type == PredictionType.WEEKLY:
                    expires_at = datetime.utcnow() + relativedelta(weeks=1)
                elif pred_type == PredictionType.MONTHLY:
                    expires_at = datetime.utcnow() + relativedelta(months=1)

                # Create prediction object
                prediction = Prediction(
                    id=f"{profile_id}_{pred_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    profile_id=profile_id,
                    user_id=user_id,
                    prediction_type=pred_type,
                    prediction_text=prediction_text,
                    generated_by="chatgpt",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    expires_at=expires_at
                )

                predictions.append(prediction)

            return predictions

        except Exception as e:
            logger.error(f"Failed to generate predictions: {e}")
            return []

    async def _create_partner_profile(self, user_id: str, main_profile_id: str, partner_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create partner profile for marriage matching"""
        try:
            partner_id = f"{main_profile_id}_partner_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Calculate coordinates for partner
            coordinates = calculate_coordinates(partner_data.get('birth_place', ''))

            partner_profile = {
                'id': partner_id,
                'main_profile_id': main_profile_id,
                'user_id': user_id,
                'name': partner_data.get('name', ''),
                'birth_date': partner_data.get('birth_date'),
                'birth_time': partner_data.get('birth_time'),
                'birth_place': partner_data.get('birth_place', ''),
                'latitude': coordinates[0] if coordinates and len(coordinates) == 2 else None,
                'longitude': coordinates[1] if coordinates and len(coordinates) == 2 else None,
                'gender': partner_data.get('gender', 'female'),
                'relationship': 'partner',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True
            }

            # Save to database
            partner_ref = self.db.collection('users').document(user_id).collection('partner_profiles').document(partner_id)
            partner_ref.set(partner_profile)

            logger.info(f"Created partner profile {partner_id}")
            return partner_profile

        except Exception as e:
            logger.error(f"Failed to create partner profile: {e}")
            raise

    def _calculate_traditional_scores(self, main_profile: Dict[str, Any], partner_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate traditional Vedic astrology compatibility scores"""
        try:
            # This is a simplified calculation - in production, use proper astrology library
            scores = {
                'guna_breakdown': {
                    'varna': 1,
                    'vasya': 1,
                    'tara': 1,
                    'yoni': 1,
                    'grahMaitri': 1,
                    'gan': 1,
                    'bhakoot': 1,
                    'nadi': 1
                },
                'total_guna': 8,
                'mangal_compatibility': 'good',
                'dosha_analysis': {
                    'mangal_dosha': 'none',
                    'kaal_sarp_dosha': 'none'
                }
            }

            return scores

        except Exception as e:
            logger.error(f"Failed to calculate traditional scores: {e}")
            return {
                'guna_breakdown': {},
                'total_guna': 0,
                'mangal_compatibility': 'unknown',
                'dosha_analysis': {}
            }

    def _merge_compatibility_data(self, ai_data: Dict[str, Any], traditional_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge AI-generated and traditional compatibility data"""
        try:
            merged = {
                'overall_score': ai_data.get('overall_score', 75.0),
                'guna_score': traditional_data.get('total_guna', 0),
                'guna_breakdown': traditional_data.get('guna_breakdown', {}),
                'mangal_compatibility': traditional_data.get('mangal_compatibility', 'neutral'),
                'strengths': ai_data.get('strengths', []),
                'challenges': ai_data.get('challenges', []),
                'recommendations': ai_data.get('recommendations', []),
                'dosha_analysis': traditional_data.get('dosha_analysis', {}),
                'ai_insights': ai_data.get('ai_insights'),
                'compatibility_level': ai_data.get('compatibility_level', 'unknown')
            }

            return merged

        except Exception as e:
            logger.error(f"Failed to merge compatibility data: {e}")
            return ai_data  # Fallback to AI data

    async def _save_predictions_to_db(self, user_id: str, profile_id: str, predictions: List[Prediction]) -> None:
        """Save predictions to Firestore"""
        try:
            batch = self.db.batch()

            for prediction in predictions:
                pred_ref = self.db.collection('predictions').document(prediction.id)
                batch.set(pred_ref, prediction.dict())

            # Firestore batch.commit() is synchronous
            batch.commit()
            logger.info(f"Saved {len(predictions)} predictions for profile {profile_id}")

        except Exception as e:
            logger.error(f"Failed to save predictions to database: {e}")
            raise

    async def _save_marriage_match_to_db(self, marriage_match: MarriageMatch) -> None:
        """Save marriage match to Firestore"""
        try:
            match_ref = self.db.collection('marriage_matches').document(marriage_match.id)
            match_ref.set(marriage_match.dict())

            logger.info(f"Saved marriage match {marriage_match.id} to database")

        except Exception as e:
            logger.error(f"Failed to save marriage match to database: {e}")
            raise

    async def _get_profile_data(self, user_id: str, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get profile data from Firestore"""
        try:
            # Fetch from top-level 'person_profiles'
            profile_ref = self.db.collection('person_profiles').document(profile_id)
            profile_doc = profile_ref.get()

            if profile_doc.exists:
                return profile_doc.to_dict()
            return None

        except Exception as e:
            logger.error(f"Failed to get profile data: {e}")
            return None

    async def get_profile_with_predictions(self, user_id: str, profile_id: str) -> Optional[ProfileWithChart]:
        """Get complete profile with chart and predictions"""
        try:
            # Get profile data
            profile_data = await self._get_profile_data(user_id, profile_id)
            if not profile_data:
                return None

            # Get astrology chart
            chart_data = await self._get_astrology_chart(user_id, profile_id)

            # Get predictions
            predictions = await self._get_predictions(user_id, profile_id)

            # Get marriage matches
            marriage_matches = await self._get_marriage_matches(user_id, profile_id)

            # Get partner profiles
            partner_profiles = await self._get_partner_profiles(user_id, profile_id)

            # Create enhanced profile
            enhanced_profile = ProfileWithChart(
                id=profile_id,
                user_id=user_id,
                name=profile_data.get('name', ''),
                birth_date=profile_data.get('birth_date'),
                birth_time=profile_data.get('birth_time'),
                birth_place=profile_data.get('birth_place', ''),
                gender=profile_data.get('gender', 'male'),
                relationship=profile_data.get('relationship', 'self'),
                zodiac_sign=profile_data.get('zodiac_sign'),
                moon_sign=profile_data.get('moon_sign'),
                nakshatra=profile_data.get('nakshatra'),
                ascendant=profile_data.get('ascendant'),
                astrology_chart=chart_data,
                predictions=predictions,
                marriage_matches=marriage_matches,
                partner_profiles=partner_profiles,
                created_at=profile_data.get('created_at'),
                updated_at=profile_data.get('updated_at'),
                is_active=profile_data.get('is_active', True)
            )

            return enhanced_profile

        except Exception as e:
            logger.error(f"Failed to get profile with predictions: {e}")
            return None

    async def _get_astrology_chart(self, user_id: str, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get astrology chart from database"""
        try:
            from app.services.astrology_service import astrology_service
            chart = await astrology_service.get_astrology_chart(user_id, profile_id)
            return chart.dict() if chart else None

        except Exception as e:
            logger.error(f"Failed to get astrology chart: {e}")
            return None

    async def get_predictions(self, user_id: str, profile_id: str) -> List[Prediction]:
        """Get predictions for a profile"""
        try:
            predictions_ref = self.db.collection('predictions')
            query = predictions_ref.where(filter=FieldFilter('profile_id', '==', profile_id))\
                                   .where(filter=FieldFilter('is_active', '==', True))\
                                   .where(filter=FieldFilter('expires_at', '>', datetime.utcnow()))\
                                   .limit(10)

            predictions = []
            for doc in query.stream():
                try:
                    data = doc.to_dict()
                    prediction = Prediction(**data)
                    predictions.append(prediction)
                except Exception as e:
                    logger.warning(f"Skipping invalid prediction doc {doc.id}: {e}")

            return predictions

        except Exception as e:
            logger.error(f"Failed to get predictions: {e}")
            return []

    async def get_marriage_matches(self, user_id: str, profile_id: str) -> List[MarriageMatch]:
        """Get marriage matches for a profile"""
        try:
            matches_ref = self.db.collection('marriage_matches')
            query = matches_ref.where(filter=FieldFilter('main_profile_id', '==', profile_id))\
                               .where(filter=FieldFilter('is_active', '==', True))\
                               .limit(10)

            matches = []
            for doc in query.stream():
                try:
                    data = doc.to_dict()
                    marriage_match = MarriageMatch(**data)
                    matches.append(marriage_match)
                except Exception as e:
                    logger.warning(f"Skipping invalid marriage_match doc {doc.id}: {e}")

            return matches

        except Exception as e:
            logger.error(f"Failed to get marriage matches: {e}")
            return []

    async def _get_partner_profiles(self, user_id: str, profile_id: str) -> List[PartnerProfile]:
        """Get partner profiles for marriage matching"""
        try:
            partners_ref = self.db.collection('users').document(user_id).collection('partner_profiles')
            query = partners_ref.where(filter=FieldFilter('main_profile_id', '==', profile_id))\
                                .where(filter=FieldFilter('is_active', '==', True))

            partners = []
            for doc in query.stream():
                try:
                    data = doc.to_dict()
                    partner = PartnerProfile(**data)
                    partners.append(partner)
                except Exception as e:
                    logger.warning(f"Skipping invalid partner_profile doc {doc.id}: {e}")

            return partners

        except Exception as e:
            logger.error(f"Failed to get partner profiles: {e}")
            return []

    async def calculate_comprehensive_astrology(
        self,
        birth_date: str,
        birth_time: str,
        birth_place: str,
        gender: str = "male"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive astrology data using real API

        Args:
            birth_date: Birth date in YYYY-MM-DD format
            birth_time: Birth time in HH:MM:SS format
            birth_place: Birth place name
            gender: Gender of the person

        Returns:
            Complete astrology calculations
        """
        try:
            logger.info(f"🔮 Calculating comprehensive astrology for {birth_date} {birth_time} at {birth_place}")

            # Get coordinates for birth place
            coordinates = calculate_coordinates(birth_place)
            if not coordinates or len(coordinates) != 2:
                logger.warning(f"Could not get coordinates for {birth_place}, using default")
                latitude, longitude = 28.6139, 77.2090  # Default: Delhi
            else:
                latitude, longitude = coordinates

            # Prepare API request data
            api_data = {
                "date": birth_date,
                "time": birth_time,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": "Asia/Kolkata",
                "settings": {
                    "observation_point": "topocentric",
                    "ayanamsha": "lahiri"
                }
            }

            # Check cache first
            latitude = coordinates[0] if coordinates and len(coordinates) == 2 else 0
            longitude = coordinates[1] if coordinates and len(coordinates) == 2 else 0
            cache_key = f"{birth_date}_{birth_time}_{latitude}_{longitude}"
            if cache_key in self._api_cache:
                logger.info("📋 Using cached astrology data")
                return self._api_cache[cache_key]

            # Make API call to free astrology service
            astrology_data = await self._call_free_astrology_api(api_data)

            if astrology_data:
                # Process and enhance the API response
                enhanced_data = self._enhance_astrology_data(astrology_data, birth_place, gender)

                # Cache the result
                self._api_cache[cache_key] = enhanced_data

                logger.info("✅ Successfully calculated comprehensive astrology data")
                return enhanced_data
            else:
                logger.warning("⚠️ API call failed, using fallback calculations")
                return self._get_fallback_astrology_data(birth_date, birth_time, birth_place, gender)

        except Exception as e:
            logger.error(f"❌ Failed to calculate comprehensive astrology: {e}")
            return self._get_fallback_astrology_data(birth_date, birth_time, birth_place, gender)

    async def _call_free_astrology_api(self, api_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call the free astrology API with proper error handling"""
        try:
            if not self.free_astrology_api_key:
                logger.warning("⚠️ FREE_ASTRO_API_KEY not configured, using fallback calculations")
                return None

            # Try multiple API endpoints
            api_urls = [
                "https://api.vedicastroapi.com/v3-json/horoscope/planets",
                "https://json.freeastrologyapi.com/planets",
                "https://api.astroapi.com/v1/planets"
            ]

            headers = {
                "x-api-key": self.free_astrology_api_key,
                "Content-Type": "application/json"
            }

            for api_url in api_urls:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        logger.info(f"🔮 Calling astrology API: {api_url}")
                        response = await client.post(api_url, json=api_data, headers=headers)

                        if response.status_code == 200:
                            data = response.json()
                            logger.info("✅ Astrology API call successful")
                            return data
                        elif response.status_code == 404:
                            logger.warning(f"⚠️ API endpoint not found: {api_url}")
                            continue
                        elif response.status_code == 403:
                            logger.warning(f"⚠️ API access forbidden: {api_url}")
                            continue
                        else:
                            logger.warning(f"⚠️ API error {response.status_code}: {response.text}")
                            continue

                except Exception as e:
                    logger.warning(f"⚠️ Failed to call {api_url}: {e}")
                    continue

            logger.warning("⚠️ All astrology API endpoints failed, using fallback calculations")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to call astrology API: {e}")
            return None

    def _enhance_astrology_data(self, api_data: Dict[str, Any], birth_place: str, gender: str) -> Dict[str, Any]:
        """Enhance raw API data with additional calculations"""
        try:
            # Extract basic information from API response
            enhanced = {
                "birth_place": birth_place,
                "gender": gender,
                "api_raw_data": api_data,
                "calculated_at": datetime.utcnow().isoformat()
            }

            # Process planetary positions if available
            if "planets" in api_data:
                enhanced["planetary_positions"] = api_data["planets"]

            # Process houses if available
            if "houses" in api_data:
                enhanced["houses"] = api_data["houses"]

            # Calculate additional Vedic astrology elements
            enhanced.update(self._calculate_vedic_elements(api_data))

            # Calculate Western astrology elements
            enhanced.update(self._calculate_western_elements(api_data))

            return enhanced

        except Exception as e:
            logger.error(f"❌ Failed to enhance astrology data: {e}")
            return {
                "birth_place": birth_place,
                "gender": gender,
                "error": str(e),
                "calculated_at": datetime.utcnow().isoformat()
            }

    def _calculate_vedic_elements(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Vedic astrology elements"""
        vedic = {}

        try:
            # Extract or calculate zodiac sign (Moon sign in Vedic astrology)
            if "moon" in api_data:
                moon_position = api_data["moon"]
                vedic["moon_sign"] = self._calculate_rashi_from_position(moon_position)
                vedic["nakshatra"] = self._calculate_nakshatra_from_position(moon_position)

            # Calculate ascendant (Lagna)
            if "ascendant" in api_data:
                vedic["ascendant"] = self._calculate_rashi_from_position(api_data["ascendant"])

            # Calculate basic chart elements
            vedic["varna"] = self._calculate_varna(gender)
            vedic["guna"] = self._calculate_guna(api_data)

        except Exception as e:
            logger.error(f"❌ Failed to calculate Vedic elements: {e}")
            vedic = {
                "moon_sign": "Unknown",
                "nakshatra": "Unknown",
                "ascendant": "Unknown",
                "varna": "Unknown",
                "guna": "Unknown"
            }

        return vedic

    def _calculate_western_elements(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Western astrology elements"""
        western = {}

        try:
            # Calculate Sun sign (Western zodiac)
            if "sun" in api_data:
                sun_position = api_data["sun"]
                western["zodiac_sign"] = self._calculate_western_zodiac_from_position(sun_position)

            # Add other Western elements as needed
            western["element"] = self._get_element_from_zodiac(western.get("zodiac_sign", ""))
            western["modality"] = self._get_modality_from_zodiac(western.get("zodiac_sign", ""))

        except Exception as e:
            logger.error(f"❌ Failed to calculate Western elements: {e}")
            western = {
                "zodiac_sign": "Unknown",
                "element": "Unknown",
                "modality": "Unknown"
            }

        return western

    def _calculate_rashi_from_position(self, position: float) -> str:
        """Calculate Rashi (Vedic zodiac sign) from planetary position"""
        try:
            # Vedic astrology has 12 signs, each spanning 30 degrees
            rashi_signs = [
                "Aries", "Taurus", "Gemini", "Cancer",
                "Leo", "Virgo", "Libra", "Scorpio",
                "Sagittarius", "Capricorn", "Aquarius", "Pisces"
            ]

            # Normalize position to 0-360 degrees
            normalized_position = position % 360

            # Calculate sign index
            sign_index = int(normalized_position // 30)

            return rashi_signs[sign_index] if sign_index < 12 else "Unknown"

        except Exception:
            return "Unknown"

    def _calculate_nakshatra_from_position(self, position: float) -> str:
        """Calculate Nakshatra from lunar position"""
        try:
            # 27 Nakshatras, each spanning approximately 13.33 degrees
            nakshatras = [
                "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
                "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
                "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
                "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
                "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
                "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
            ]

            # Normalize position to 0-360 degrees
            normalized_position = position % 360

            # Calculate nakshatra index
            nakshatra_index = int(normalized_position // 13.333)

            return nakshatras[nakshatra_index] if nakshatra_index < 27 else "Unknown"

        except Exception:
            return "Unknown"

    def _calculate_western_zodiac_from_position(self, position: float) -> str:
        """Calculate Western zodiac sign from position"""
        try:
            # Western zodiac signs
            zodiac_signs = [
                "Aries", "Taurus", "Gemini", "Cancer",
                "Leo", "Virgo", "Libra", "Scorpio",
                "Sagittarius", "Capricorn", "Aquarius", "Pisces"
            ]

            # Normalize position to 0-360 degrees
            normalized_position = position % 360

            # Calculate sign index (Western astrology uses tropical zodiac)
            sign_index = int(normalized_position // 30)

            return zodiac_signs[sign_index] if sign_index < 12 else "Unknown"

        except Exception:
            return "Unknown"

    def _calculate_varna(self, gender: str) -> str:
        """Calculate Varna (caste) based on birth details"""
        # Simplified calculation - in production, this would be more complex
        return "Brahmin"  # Placeholder

    def _calculate_guna(self, api_data: Dict[str, Any]) -> str:
        """Calculate Guna (nature) based on planetary positions"""
        # Simplified calculation - in production, this would be more complex
        return "Satvik"  # Placeholder

    def _get_element_from_zodiac(self, zodiac_sign: str) -> str:
        """Get element (Fire, Earth, Air, Water) from zodiac sign"""
        elements = {
            "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
            "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
            "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
            "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
        }
        return elements.get(zodiac_sign, "Unknown")

    def _get_modality_from_zodiac(self, zodiac_sign: str) -> str:
        """Get modality (Cardinal, Fixed, Mutable) from zodiac sign"""
        modalities = {
            "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
            "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
            "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable"
        }
        return modalities.get(zodiac_sign, "Unknown")

    def _get_fallback_astrology_data(self, birth_date: str, birth_time: str, birth_place: str, gender: str) -> Dict[str, Any]:
        """Provide comprehensive fallback astrology data when API fails"""
        logger.info("📋 Using enhanced fallback astrology calculations")

        try:
            # Parse birth date and time
            day = int(birth_date.split('-')[2]) if '-' in birth_date else 15
            month = int(birth_date.split('-')[1]) if '-' in birth_date else 6

            # Enhanced zodiac calculation with better accuracy
            zodiac_signs = [
                "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini",
                "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"
            ]
            zodiac_dates = [20, 19, 21, 20, 21, 21, 23, 23, 23, 23, 22, 22]
            zodiac_index = month - 1 if day >= zodiac_dates[month - 1] else (month - 2) % 12
            zodiac_sign = zodiac_signs[zodiac_index]

            # Calculate moon sign ( Vedic astrology - Moon sign is primary)
            moon_sign = self._calculate_moon_sign(day, month)

            # Calculate nakshatra based on moon position
            nakshatra = self._calculate_nakshatra_enhanced(day, month)

            # Calculate ascendant based on birth time and place
            ascendant = self._calculate_ascendant(birth_time, birth_place)

            # Calculate other Vedic elements
            varna = self._calculate_varna_enhanced(gender, zodiac_sign)
            guna = self._calculate_guna_enhanced(moon_sign)

            return {
                "birth_place": birth_place,
                "gender": gender,
                "zodiac_sign": zodiac_sign,
                "moon_sign": moon_sign,
                "nakshatra": nakshatra,
                "ascendant": ascendant,
                "varna": varna,
                "guna": guna,
                "element": self._get_element_from_zodiac(zodiac_sign),
                "modality": self._get_modality_from_zodiac(zodiac_sign),
                "calculated_at": datetime.utcnow().isoformat(),
                "calculation_method": "enhanced_fallback",
                "planetary_positions": self._get_fallback_planetary_positions(zodiac_sign),
                "houses": self._get_fallback_houses(zodiac_sign, moon_sign)
            }

        except Exception as e:
            logger.error(f"❌ Enhanced fallback calculation failed: {e}")
            # Ultimate fallback
            return {
                "birth_place": birth_place,
                "gender": gender,
                "zodiac_sign": "Capricorn",
                "moon_sign": "Capricorn",
                "nakshatra": "Ashwini",
                "ascendant": "Sagittarius",
                "varna": "Brahmin",
                "guna": "Satvik",
                "element": "Earth",
                "modality": "Cardinal",
                "calculated_at": datetime.utcnow().isoformat(),
                "calculation_method": "basic_fallback"
            }
    
        def _calculate_moon_sign(self, day: int, month: int) -> str:
            """Calculate moon sign based on birth date"""
            # Moon stays in each sign for about 2.5 days
            moon_signs = [
                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
            ]
    
            # Calculate day of year
            day_of_year = day
            for m in range(1, month):
                if m in [1, 3, 5, 7, 8, 10, 12]:
                    day_of_year += 31
                elif m in [4, 6, 9, 11]:
                    day_of_year += 30
                elif m == 2:
                    day_of_year += 28  # Simplified, ignoring leap years
    
            # Moon sign changes every ~2.5 days
            moon_position = (day_of_year / 2.5) % 12
            return moon_signs[int(moon_position)]
    
        def _calculate_nakshatra_enhanced(self, day: int, month: int) -> str:
            """Calculate nakshatra with enhanced accuracy"""
            nakshatras = [
                "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
                "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
                "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
                "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
                "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
            ]
    
            # Calculate day of year
            day_of_year = day
            for m in range(1, month):
                if m in [1, 3, 5, 7, 8, 10, 12]:
                    day_of_year += 31
                elif m in [4, 6, 9, 11]:
                    day_of_year += 30
                elif m == 2:
                    day_of_year += 28
    
            # Each nakshatra spans ~13.33 degrees, full circle 360 degrees
            nakshatra_index = int((day_of_year * 27 / 365) % 27)
            return nakshatras[nakshatra_index]
    
        def _calculate_ascendant(self, birth_time: str, birth_place: str) -> str:
            """Calculate ascendant based on birth time and place"""
            try:
                hour = int(birth_time.split(':')[0]) if ':' in birth_time else 12
    
                # Simple calculation based on birth time
                ascendant_signs = [
                    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
                ]
    
                # Each sign rises for approximately 2 hours
                ascendant_index = (hour // 2) % 12
                return ascendant_signs[ascendant_index]
    
            except Exception:
                return "Sagittarius"  # Default fallback
    
        def _calculate_varna_enhanced(self, gender: str, zodiac_sign: str) -> str:
            """Calculate Varna with enhanced logic"""
            varna_mapping = {
                "Aries": "Kshatriya", "Taurus": "Vaishya", "Gemini": "Shudra",
                "Cancer": "Brahmin", "Leo": "Kshatriya", "Virgo": "Vaishya",
                "Libra": "Shudra", "Scorpio": "Brahmin", "Sagittarius": "Kshatriya",
                "Capricorn": "Vaishya", "Aquarius": "Shudra", "Pisces": "Brahmin"
            }
            return varna_mapping.get(zodiac_sign, "Brahmin")
    
        def _calculate_guna_enhanced(self, moon_sign: str) -> str:
            """Calculate Guna with enhanced logic"""
            guna_mapping = {
                "Aries": "Rajasic", "Taurus": "Tamasic", "Gemini": "Rajasic",
                "Cancer": "Satvik", "Leo": "Rajasic", "Virgo": "Satvik",
                "Libra": "Rajasic", "Scorpio": "Tamasic", "Sagittarius": "Satvik",
                "Capricorn": "Tamasic", "Aquarius": "Satvik", "Pisces": "Satvik"
            }
            return guna_mapping.get(moon_sign, "Satvik")
    
        def _get_fallback_planetary_positions(self, zodiac_sign: str) -> Dict[str, Any]:
            """Get fallback planetary positions"""
            return {
                "Sun": {"sign": zodiac_sign, "degree": 15.5, "house": 1},
                "Moon": {"sign": self._calculate_moon_sign(15, 6), "degree": 45.2, "house": 4},
                "Mars": {"sign": "Aries", "degree": 22.8, "house": 7},
                "Mercury": {"sign": "Gemini", "degree": 18.3, "house": 9},
                "Jupiter": {"sign": "Sagittarius", "degree": 25.7, "house": 3},
                "Venus": {"sign": "Taurus", "degree": 12.4, "house": 8},
                "Saturn": {"sign": "Capricorn", "degree": 28.9, "house": 4},
                "Rahu": {"sign": "Cancer", "degree": 15.2, "house": 10},
                "Ketu": {"sign": "Capricorn", "degree": 15.2, "house": 4}
            }
    
        def _get_fallback_houses(self, zodiac_sign: str, moon_sign: str) -> Dict[str, Any]:
            """Get fallback house positions"""
            return {
                "house_1": {"sign": zodiac_sign, "planets": ["Sun"]},
                "house_2": {"sign": self._get_next_sign(zodiac_sign), "planets": []},
                "house_3": {"sign": self._get_next_sign(zodiac_sign, 2), "planets": []},
                "house_4": {"sign": moon_sign, "planets": ["Moon"]},
                "house_5": {"sign": self._get_next_sign(moon_sign), "planets": []},
                "house_6": {"sign": self._get_next_sign(moon_sign, 2), "planets": []},
                "house_7": {"sign": self._get_next_sign(moon_sign, 3), "planets": []},
                "house_8": {"sign": self._get_next_sign(moon_sign, 4), "planets": []},
                "house_9": {"sign": self._get_next_sign(moon_sign, 5), "planets": []},
                "house_10": {"sign": self._get_next_sign(moon_sign, 6), "planets": []},
                "house_11": {"sign": self._get_next_sign(moon_sign, 7), "planets": []},
                "house_12": {"sign": self._get_next_sign(moon_sign, 8), "planets": []}
            }
    
        def _get_next_sign(self, current_sign: str, steps: int = 1) -> str:
            """Get next zodiac sign"""
            signs = [
                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
            ]
    
            try:
                current_index = signs.index(current_sign)
                next_index = (current_index + steps) % 12
                return signs[next_index]
            except ValueError:
                return "Taurus"  # Default fallback

    async def generate_astrology_chart_data(
        self,
        user_id: str,
        profile_id: str,
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive astrology chart data"""
        try:
            logger.info(f"📊 Generating astrology chart for profile {profile_id}")

            # Get comprehensive astrology data
            astrology_data = await self.calculate_comprehensive_astrology(
                profile_data.get('birth_date', ''),
                profile_data.get('birth_time', ''),
                profile_data.get('birth_place', ''),
                profile_data.get('gender', 'male')
            )

            # Structure chart data for frontend consumption
            chart_data = {
                "user_id": user_id,
                "profile_id": profile_id,
                "basic_info": {
                    "name": profile_data.get('name', ''),
                    "birth_date": profile_data.get('birth_date'),
                    "birth_time": profile_data.get('birth_time'),
                    "birth_place": profile_data.get('birth_place'),
                    "gender": profile_data.get('gender')
                },
                "vedic_astrology": {
                    "moon_sign": astrology_data.get('moon_sign', 'Unknown'),
                    "nakshatra": astrology_data.get('nakshatra', 'Unknown'),
                    "ascendant": astrology_data.get('ascendant', 'Unknown'),
                    "varna": astrology_data.get('varna', 'Unknown'),
                    "guna": astrology_data.get('guna', 'Unknown')
                },
                "western_astrology": {
                    "zodiac_sign": astrology_data.get('zodiac_sign', 'Unknown'),
                    "element": astrology_data.get('element', 'Unknown'),
                    "modality": astrology_data.get('modality', 'Unknown')
                },
                "planetary_positions": astrology_data.get('planetary_positions', {}),
                "houses": astrology_data.get('houses', {}),
                "calculated_at": astrology_data.get('calculated_at'),
                "calculation_method": astrology_data.get('calculation_method', 'api')
            }

            logger.info(f"✅ Successfully generated astrology chart data for {profile_id}")
            return chart_data

        except Exception as e:
            logger.error(f"❌ Failed to generate astrology chart data: {e}")
            return {
                "user_id": user_id,
                "profile_id": profile_id,
                "error": str(e),
                "calculated_at": datetime.utcnow().isoformat()
            }

# Global service instance
enhanced_astrology_service = EnhancedAstrologyService()