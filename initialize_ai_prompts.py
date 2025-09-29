#!/usr/bin/env python3
"""
Initialize AI Prompts in Database

This script saves the marriage compatibility prompt and other AI prompts
to the Firestore database for consistent use across the application.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.firebase import get_firestore_client, initialize_firebase

async def initialize_ai_prompts():
    """Initialize AI prompts in the database"""
    try:
        # Initialize Firebase
        initialize_firebase()
        db = get_firestore_client()

        print("🔄 Initializing AI prompts in database...")

        # Marriage compatibility prompt
        marriage_prompt = """
You are Zodira – a Vedic Astrology AI specialized in marriage compatibility analysis.
Your task is to generate a complete marriage matching report for the given bride and groom data.

Instructions:

    Inputs Provided:

        Bride & Groom full horoscope charts (Rasi, Navamsa, D10, etc.).

        Birth details: date, time, place (with latitude, longitude, timezone).

        Porutham compatibility factors (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi).

        Nakshatra Porutham factors (Dina, Gana, Mahendra, Sthree Deergha, Yoni, Rasi, Rasi Adhipathi, Vasya, Rajju, Vedha).

        Vimshottari Dasha–Bukthi sequences.

    Tasks:

        Compute Katta Porutham score (out of 36).

        Compute Nakshatra Porutham score (out of 10).

        Check for Manglik / Kuja Dosha in both charts (1st, 2nd, 4th, 7th, 8th, 12th house from Lagna, Moon, Venus).

            Mention if Dosha gets cancelled due to cancellation rules.

        Compare both charts' Dasha–Bukthi overlaps (especially Venus, Mars, Rahu, Saturn) to see if marital harmony is supported or strained.

        Generate Character Profiles:

            Personality traits (mental nature, emotional strength, communication style, family orientation).

            Career tendencies.

            Financial approach (spending vs saving).

            Spiritual/ethical alignment.

    Output Format:

        Overall Compatibility Score (out of 100).

        Katta Porutham (8 factors) → show individual factor scores with explanation.

        Nakshatra Porutham (10 factors) → show factor verdicts with explanation.

        Manglik / Kuja Dosha:

            Present for bride? yes/no, with reasoning.

            Present for groom? yes/no, with reasoning.

            Cancellation rules applied? yes/no.

        Dasha–Bukthi Compatibility:

            List key overlapping periods (with years).

            Highlight supportive vs challenging combinations.

        Character Profiles:

            Bride (summary of traits).

            Groom (summary of traits).

            Compatibility verdict on personalities.

        Final Verdict:

            Excellent / Very Good / Moderate / Challenging.

            Provide marriage guidance if needed (e.g., remedies, rituals).

    Tone:

        Professional, clear, non-superstitious, easy to understand.

        Highlight positives, but explain challenges honestly.

        Suggest remedies if severe dosha is found.

Bride Details:
- Name: {MAIN_NAME}
- Birth Date: {MAIN_BIRTH_DATE}
- Birth Time: {MAIN_BIRTH_TIME}
- Birth Place: {MAIN_BIRTH_PLACE}
- Zodiac Sign: {MAIN_ZODIAC_SIGN}
- Moon Sign: {MAIN_MOON_SIGN}
- Gender: {MAIN_GENDER}

Groom Details:
- Name: {PARTNER_NAME}
- Birth Date: {PARTNER_BIRTH_DATE}
- Birth Time: {PARTNER_BIRTH_TIME}
- Birth Place: {PARTNER_BIRTH_PLACE}
- Zodiac Sign: {PARTNER_ZODIAC_SIGN}
- Moon Sign: {PARTNER_MOON_SIGN}
- Gender: {PARTNER_GENDER}

Chart Data:
Bride Chart: {MAIN_CHART_DATA}
Groom Chart: {PARTNER_CHART_DATA}

Please provide a comprehensive marriage compatibility analysis following the exact format specified above.
"""

        # Save marriage compatibility prompt
        marriage_ref = db.collection('ai_prompts').document('marriage_compatibility')
        marriage_ref.set({
            'prompt': marriage_prompt,
            'name': 'Marriage Compatibility Analysis',
            'description': 'Comprehensive Vedic astrology marriage compatibility analysis prompt',
            'version': '1.0',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        })

        print("✅ Marriage compatibility prompt saved to database")

        # Daily prediction prompt
        daily_prediction_prompt = """
You are Zodira – a Vedic Astrology AI specialized in daily predictions.
Generate a personalized daily astrology prediction for the given person.

Person Details:
- Name: {USER_NAME}
- Birth Date: {BIRTH_DATE}
- Birth Time: {BIRTH_TIME}
- Birth Place: {BIRTH_PLACE}
- Zodiac Sign: {ZODIAC_SIGN}
- Moon Sign: {MOON_SIGN}
- Gender: {GENDER}

Chart Data: {CHART_DATA}

Please provide a detailed daily prediction covering:
1. Overall outlook for today
2. Career and professional matters
3. Health and well-being
4. Relationships and personal life
5. Financial matters
6. Lucky numbers, colors, and directions
7. Any precautions or remedies

Make the prediction personal, positive, and actionable. Use traditional Vedic astrology principles.
"""

        daily_ref = db.collection('ai_prompts').document('daily_prediction')
        daily_ref.set({
            'prompt': daily_prediction_prompt,
            'name': 'Daily Prediction',
            'description': 'Daily astrology prediction prompt',
            'version': '1.0',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        })

        print("✅ Daily prediction prompt saved to database")

        # Weekly prediction prompt
        weekly_prediction_prompt = """
You are Zodira – a Vedic Astrology AI specialized in weekly predictions.
Generate a personalized weekly astrology prediction for the given person.

Person Details:
- Name: {USER_NAME}
- Birth Date: {BIRTH_DATE}
- Birth Time: {BIRTH_TIME}
- Birth Place: {BIRTH_PLACE}
- Zodiac Sign: {ZODIAC_SIGN}
- Moon Sign: {MOON_SIGN}
- Gender: {GENDER}

Chart Data: {CHART_DATA}

Please provide a detailed weekly prediction covering:
1. Overall outlook for the week
2. Career opportunities and challenges
3. Health and wellness guidance
4. Relationship dynamics
5. Financial planning and decisions
6. Lucky numbers, colors, and directions
7. Important dates and timing
8. Spiritual and personal growth

Focus on opportunities and provide practical guidance for the week ahead.
"""

        weekly_ref = db.collection('ai_prompts').document('weekly_prediction')
        weekly_ref.set({
            'prompt': weekly_prediction_prompt,
            'name': 'Weekly Prediction',
            'description': 'Weekly astrology prediction prompt',
            'version': '1.0',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        })

        print("✅ Weekly prediction prompt saved to database")

        # Career prediction prompt
        career_prediction_prompt = """
You are Zodira – a Vedic Astrology AI specialized in career predictions.
Generate a personalized career astrology prediction for the given person.

Person Details:
- Name: {USER_NAME}
- Birth Date: {BIRTH_DATE}
- Birth Time: {BIRTH_TIME}
- Birth Place: {BIRTH_PLACE}
- Zodiac Sign: {ZODIAC_SIGN}
- Moon Sign: {MOON_SIGN}
- Gender: {GENDER}

Chart Data: {CHART_DATA}

Please provide a detailed career prediction covering:
1. Career direction and opportunities
2. Professional relationships and networking
3. Leadership and management potential
4. Financial growth and stability
5. Skill development and learning
6. Work-life balance considerations
7. Potential challenges and solutions
8. Long-term career trajectory

Provide practical, actionable career guidance based on Vedic astrology principles.
"""

        career_ref = db.collection('ai_prompts').document('career_prediction')
        career_ref.set({
            'prompt': career_prediction_prompt,
            'name': 'Career Prediction',
            'description': 'Career astrology prediction prompt',
            'version': '1.0',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        })

        print("✅ Career prediction prompt saved to database")

        # Health prediction prompt
        health_prediction_prompt = """
You are Zodira – a Vedic Astrology AI specialized in health predictions.
Generate a personalized health astrology prediction for the given person.

Person Details:
- Name: {USER_NAME}
- Birth Date: {BIRTH_DATE}
- Birth Time: {BIRTH_TIME}
- Birth Place: {BIRTH_PLACE}
- Zodiac Sign: {ZODIAC_SIGN}
- Moon Sign: {MOON_SIGN}
- Gender: {GENDER}

Chart Data: {CHART_DATA}

Please provide a detailed health prediction covering:
1. Overall health and vitality
2. Specific health areas to monitor
3. Dietary and nutrition guidance
4. Exercise and physical activity
5. Mental health and stress management
6. Preventive healthcare measures
7. Healing and recovery periods
8. Spiritual health and wellness

Provide health guidance that complements medical advice, not replaces it.
"""

        health_ref = db.collection('ai_prompts').document('health_prediction')
        health_ref.set({
            'prompt': health_prediction_prompt,
            'name': 'Health Prediction',
            'description': 'Health astrology prediction prompt',
            'version': '1.0',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        })

        print("✅ Health prediction prompt saved to database")

        print("\n🎉 All AI prompts initialized successfully!")
        print("\n📋 Summary:")
        print("   ✅ Marriage Compatibility Prompt")
        print("   ✅ Daily Prediction Prompt")
        print("   ✅ Weekly Prediction Prompt")
        print("   ✅ Career Prediction Prompt")
        print("   ✅ Health Prediction Prompt")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize AI prompts: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_prompts():
    """Verify that prompts are saved correctly"""
    try:
        print("\n🔍 Verifying saved prompts...")

        db = get_firestore_client()
        prompts_ref = db.collection('ai_prompts')
        docs = prompts_ref.stream()

        prompt_count = 0
        for doc in docs:
            data = doc.to_dict()
            print(f"✅ {data.get('name', doc.id)}: {len(data.get('prompt', ''))} characters")
            prompt_count += 1

        print(f"\n📊 Total prompts saved: {prompt_count}")
        return True

    except Exception as e:
        print(f"❌ Failed to verify prompts: {e}")
        return False

async def main():
    """Main initialization function"""
    print("🚀 ZODIRA AI Prompts Database Initialization")
    print("=" * 60)

    # Initialize prompts
    success = await initialize_ai_prompts()

    if success:
        # Verify prompts
        await verify_prompts()

        print("\n✅ AI prompts initialization completed successfully!")
        print("\n🔧 Next steps:")
        print("   1. Set your OPENAI_API_KEY in .env file")
        print("   2. Run the application to test AI features")
        print("   3. Use test_complete_flow.py to verify functionality")
    else:
        print("\n❌ AI prompts initialization failed!")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)