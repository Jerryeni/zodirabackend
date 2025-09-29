"""
Enhanced Astrology Service for ZODIRA Backend

This service provides comprehensive astrology functionality including:
- Chart generation and calculations
- AI-powered predictions via ChatGPT
- Marriage compatibility analysis
- Profile management with astrology data
"""

import os
import json
import logging
from datetime import datetime, date, time
from typing import Dict, List, Optional, Any
from dateutil.relativedelta import relativedelta

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
            profile_ref = self.db.collection('users').document(user_id).collection('profiles').document(profile_id)
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

            # Convert profile data to birth details format
            birth_details = {
                'year': profile_data.get('birth_date', date.today()).year,
                'month': profile_data.get('birth_date', date.today()).month,
                'date': profile_data.get('birth_date', date.today()).day,
                'hour': profile_data.get('birth_time', time(12, 0)).hour,
                'minute': profile_data.get('birth_time', time(12, 0)).minute,
                'latitude': profile_data.get('latitude', 0),
                'longitude': profile_data.get('longitude', 0),
                'timezone': profile_data.get('timezone', 'Asia/Kolkata')
            }

            # Generate chart using existing service
            chart = await astrology_service.generate_astrology_chart(user_id, profile_id, birth_details)

            # Convert to dictionary format
            return chart.dict() if hasattr(chart, 'dict') else chart

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
                'latitude': coordinates.get('latitude') if coordinates else None,
                'longitude': coordinates.get('longitude') if coordinates else None,
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

            await batch.commit()
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
            profile_ref = self.db.collection('users').document(user_id).collection('profiles').document(profile_id)
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

    async def _get_predictions(self, user_id: str, profile_id: str) -> List[Prediction]:
        """Get predictions for a profile"""
        try:
            predictions_ref = self.db.collection('predictions')
            query = predictions_ref.where('profile_id', '==', profile_id)\
                                 .where('is_active', '==', True)\
                                 .where('expires_at', '>', datetime.utcnow())\
                                 .limit(10)

            predictions = []
            for doc in query.stream():
                data = doc.to_dict()
                prediction = Prediction(**data)
                predictions.append(prediction)

            return predictions

        except Exception as e:
            logger.error(f"Failed to get predictions: {e}")
            return []

    async def _get_marriage_matches(self, user_id: str, profile_id: str) -> List[MarriageMatch]:
        """Get marriage matches for a profile"""
        try:
            matches_ref = self.db.collection('marriage_matches')
            query = matches_ref.where('main_profile_id', '==', profile_id)\
                             .where('is_active', '==', True)\
                             .limit(10)

            matches = []
            for doc in query.stream():
                data = doc.to_dict()
                marriage_match = MarriageMatch(**data)
                matches.append(marriage_match)

            return matches

        except Exception as e:
            logger.error(f"Failed to get marriage matches: {e}")
            return []

    async def _get_partner_profiles(self, user_id: str, profile_id: str) -> List[PartnerProfile]:
        """Get partner profiles for marriage matching"""
        try:
            partners_ref = self.db.collection('users').document(user_id).collection('partner_profiles')
            query = partners_ref.where('main_profile_id', '==', profile_id)\
                              .where('is_active', '==', True)

            partners = []
            for doc in query.stream():
                data = doc.to_dict()
                partner = PartnerProfile(**data)
                partners.append(partner)

            return partners

        except Exception as e:
            logger.error(f"Failed to get partner profiles: {e}")
            return []

# Global service instance
enhanced_astrology_service = EnhancedAstrologyService()