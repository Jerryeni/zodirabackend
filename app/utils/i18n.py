"""
Internationalization (i18n) support for ZODIRA Backend

This module provides translation support for multiple languages.
"""

from typing import Dict, Any
import json
import os

class Translator:
    """Simple translation service"""

    def __init__(self):
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()

    def load_translations(self):
        """Load translation files"""
        # For now, we'll define translations inline
        # In production, load from JSON files

        self.translations = {
            'en': {
                # Authentication
                'invalid_token': 'Invalid or expired token',
                'user_not_found': 'User not found',
                'profile_not_found': 'Profile not found',
                'not_authorized': 'Not authorized to access this resource',

                # Marriage Matching
                'excellent_match': 'Excellent Match',
                'very_good_match': 'Very Good Match',
                'good_match': 'Good Match',
                'average_match': 'Average Match',
                'not_recommended': 'Not Recommended',

                # Dosha Analysis
                'manglik_dosha_present': 'Manglik dosha present due to Mars position',
                'no_manglik_dosha': 'No Manglik dosha',
                'kaal_sarp_dosha_none': 'No Kaal Sarp dosha present',

                # Recommendations
                'excellent_match_recommendation': 'This is an excellent match! You both are ideal partners for each other.',
                'good_match_recommendation': 'This is a good match. With some adjustments, this can work well.',
                'needs_improvement': 'This match needs improvement. Consult an expert before proceeding.',
                'manglik_remedies': 'Manglik dosha present. Perform appropriate remedies.',
            },
            'hi': {
                # Authentication
                'invalid_token': 'अमान्य या समाप्त टोकन',
                'user_not_found': 'उपयोगकर्ता नहीं मिला',
                'profile_not_found': 'प्रोफ़ाइल नहीं मिली',
                'not_authorized': 'इस संसाधन तक पहुंचने के लिए अधिकृत नहीं',

                # Marriage Matching
                'excellent_match': 'उत्कृष्ट मिलान',
                'very_good_match': 'बहुत अच्छा मिलान',
                'good_match': 'अच्छा मिलान',
                'average_match': 'औसत मिलान',
                'not_recommended': 'अनुशंसित नहीं',

                # Dosha Analysis
                'manglik_dosha_present': 'मंगल की स्थिति के कारण मांगलिक दोष मौजूद',
                'no_manglik_dosha': 'कोई मांगलिक दोष नहीं',
                'kaal_sarp_dosha_none': 'कोई काल सर्प दोष मौजूद नहीं',

                # Recommendations
                'excellent_match_recommendation': 'यह एक उत्कृष्ट मिलान है! आप दोनों एक दूसरे के लिए आदर्श साथी हैं।',
                'good_match_recommendation': 'यह एक अच्छा मिलान है। कुछ समायोजन के साथ यह काम कर सकता है।',
                'needs_improvement': 'इस मिलान में सुधार की आवश्यकता है। आगे बढ़ने से पहले विशेषज्ञ से सलाह लें।',
                'manglik_remedies': 'मांगलिक दोष मौजूद है। उपयुक्त उपाय करें।',
            }
        }

    def translate(self, key: str, language: str = 'en') -> str:
        """Translate a key to the specified language"""
        if language not in self.translations:
            language = 'en'  # Fallback to English

        return self.translations[language].get(key, key)

    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return list(self.translations.keys())

# Global translator instance
translator = Translator()

def _(key: str, language: str = 'en') -> str:
    """Convenience function for translation"""
    return translator.translate(key, language)