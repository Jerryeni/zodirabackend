#!/usr/bin/env python3
"""
Complete User Flow Test Script for ZODIRA Backend

This script tests the complete user journey from registration to marriage matching:
1. User registration and authentication
2. Profile creation
3. Astrology chart generation
4. AI prediction generation
5. Marriage compatibility analysis
6. Persistent session management
"""

import os
import sys
import json
import asyncio
from datetime import datetime, date, time
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.firebase import get_firestore_client, initialize_firebase
from app.services.user_service import user_service
from app.services.enhanced_astrology_service import enhanced_astrology_service
from app.services.chatgpt_service import chatgpt_service

class CompleteFlowTester:
    """Test class for complete user flow"""

    def __init__(self):
        self.db = None
        self.test_user_id = None
        self.test_profile_id = None
        self.test_session_token = None

    async def initialize(self):
        """Initialize Firebase and test environment"""
        try:
            initialize_firebase()
            self.db = get_firestore_client()
            print("✅ Firebase initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            return False

    async def test_user_registration(self):
        """Test user registration and authentication"""
        try:
            print("\n🔄 Testing User Registration...")

            # Test phone authentication
            phone_number = "+919876543210"  # Test phone number

            # Initiate authentication
            auth_result = await user_service.initiate_auth(phone_number)

            print(f"✅ Authentication initiated: {auth_result.get('status')}")

            # Simulate OTP verification (using debug OTP from response)
            otp_code = auth_result.get('debug_otp', '123456')
            session_id = auth_result.get('session_id')

            # Verify OTP
            verify_result = await user_service.verify_otp(session_id, otp_code)

            self.test_user_id = verify_result.get('user_id')
            self.test_session_token = verify_result.get('persistent_session_token')

            print(f"✅ User authenticated: {self.test_user_id}")
            print(f"✅ Persistent session created: {self.test_session_token[:20]}...")

            return True

        except Exception as e:
            print(f"❌ User registration test failed: {e}")
            return False

    async def test_profile_creation(self):
        """Test profile creation"""
        try:
            print("\n🔄 Testing Profile Creation...")

            if not self.test_user_id:
                print("❌ No user ID available")
                return False

            # Create test profile data
            profile_data = {
                'name': 'Test User',
                'birth_date': date(1990, 5, 15),
                'birth_time': time(14, 30, 0),
                'birth_place': 'Mumbai, Maharashtra, India',
                'gender': 'male',
                'userId': self.test_user_id
            }

            # Save profile to Firestore
            profiles_ref = self.db.collection('users').document(self.test_user_id).collection('profiles')
            profile_doc = profiles_ref.document()
            self.test_profile_id = profile_doc.id

            # Convert date/time objects to Firestore-compatible format
            firestore_data = {
                'id': self.test_profile_id,
                'user_id': self.test_user_id,
                'relationship': 'self',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'is_active': True,
                # Convert date/time to Firestore-compatible format
                'birth_date': profile_data['birth_date'].isoformat(),
                'birth_time': profile_data['birth_time'].isoformat(),
                'name': profile_data['name'],
                'birth_place': profile_data['birth_place'],
                'gender': profile_data['gender']
            }

            profile_doc.set(firestore_data)

            print(f"✅ Profile created: {self.test_profile_id}")
            return True

        except Exception as e:
            print(f"❌ Profile creation test failed: {e}")
            return False

    async def test_astrology_chart_generation(self):
        """Test astrology chart generation"""
        try:
            print("\n🔄 Testing Astrology Chart Generation...")

            if not self.test_user_id or not self.test_profile_id:
                print("❌ Missing user or profile ID")
                return False

            # Get profile data
            profile_ref = self.db.collection('users').document(self.test_user_id).collection('profiles').document(self.test_profile_id)
            profile_doc = profile_ref.get()

            if not profile_doc.exists:
                print("❌ Profile not found")
                return False

            profile_data = profile_doc.to_dict()

            # Generate astrology chart
            chart_data = await enhanced_astrology_service._generate_astrology_chart(
                self.test_user_id, self.test_profile_id, profile_data
            )

            print("✅ Astrology chart generated")
            print(f"   Houses: {len(chart_data.get('houses', {}))}")
            print(f"   Career data: {bool(chart_data.get('career'))}")
            print(f"   Finance data: {bool(chart_data.get('finance'))}")

            return True

        except Exception as e:
            print(f"❌ Chart generation test failed: {e}")
            return False

    async def test_ai_predictions(self):
        """Test AI prediction generation"""
        try:
            print("\n🔄 Testing AI Predictions...")

            if not self.test_user_id or not self.test_profile_id:
                print("❌ Missing user or profile ID")
                return False

            # Get profile and chart data
            profile_ref = self.db.collection('users').document(self.test_user_id).collection('profiles').document(self.test_profile_id)
            profile_doc = profile_ref.get()

            if not profile_doc.exists:
                print("❌ Profile not found")
                return False

            profile_data = profile_doc.to_dict()

            # Generate chart data
            chart_data = await enhanced_astrology_service._generate_astrology_chart(
                self.test_user_id, self.test_profile_id, profile_data
            )

            # Test different prediction types
            prediction_types = ['daily', 'weekly', 'career']

            for pred_type in prediction_types:
                prediction = await chatgpt_service.generate_personal_predictions(
                    profile_data, chart_data, pred_type
                )

                print(f"✅ Generated {pred_type} prediction ({len(prediction)} characters)")

                # Save prediction to database
                prediction_id = f"{self.test_profile_id}_{pred_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                pred_ref = self.db.collection('predictions').document(prediction_id)
                pred_ref.set({
                    'id': prediction_id,
                    'profile_id': self.test_profile_id,
                    'user_id': self.test_user_id,
                    'prediction_type': pred_type,
                    'prediction_text': prediction,
                    'generated_by': 'chatgpt',
                    'is_active': True,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })

            return True

        except Exception as e:
            print(f"❌ AI prediction test failed: {e}")
            return False

    async def test_marriage_matching(self):
        """Test marriage compatibility analysis"""
        try:
            print("\n🔄 Testing Marriage Matching...")

            if not self.test_user_id or not self.test_profile_id:
                print("❌ Missing user or profile ID")
                return False

            # Create partner data
            partner_data = {
                'name': 'Test Partner',
                'birth_date': date(1992, 8, 20),
                'birth_time': time(16, 45, 0),
                'birth_place': 'Delhi, India',
                'gender': 'female'
            }

            # Generate marriage match
            marriage_match = await enhanced_astrology_service.generate_marriage_match(
                self.test_user_id, self.test_profile_id, partner_data
            )

            print("✅ Marriage compatibility generated")
            print(f"   Overall score: {marriage_match.overall_score}")
            print(f"   Guna score: {marriage_match.guna_score}")
            print(f"   Compatibility level: {marriage_match.compatibility_level}")
            print(f"   Number of strengths: {len(marriage_match.strengths)}")
            print(f"   Number of recommendations: {len(marriage_match.recommendations)}")

            return True

        except Exception as e:
            print(f"❌ Marriage matching test failed: {e}")
            return False

    async def test_persistent_session(self):
        """Test persistent session functionality"""
        try:
            print("\n🔄 Testing Persistent Session...")

            if not self.test_session_token:
                print("❌ No session token available")
                return False

            # Test session validation
            session_data = await user_service.validate_persistent_session(self.test_session_token)

            if session_data:
                print("✅ Persistent session validated")
                print(f"   User ID: {session_data.get('user_id')}")
                print(f"   Access token generated: {bool(session_data.get('access_token'))}")
            else:
                print("❌ Persistent session validation failed")
                return False

            # Test session refresh
            refreshed_token = await user_service.refresh_persistent_session(self.test_user_id)
            if refreshed_token:
                print("✅ Session refreshed successfully")
                self.test_session_token = refreshed_token
            else:
                print("❌ Session refresh failed")

            return True

        except Exception as e:
            print(f"❌ Persistent session test failed: {e}")
            return False

    async def test_complete_flow(self):
        """Test the complete user flow"""
        try:
            print("🚀 Starting Complete User Flow Test")
            print("=" * 60)

            # Run all tests
            tests = [
                ("Firebase Initialization", self.initialize),
                ("User Registration", self.test_user_registration),
                ("Profile Creation", self.test_profile_creation),
                ("Astrology Chart Generation", self.test_astrology_chart_generation),
                ("AI Predictions", self.test_ai_predictions),
                ("Marriage Matching", self.test_marriage_matching),
                ("Persistent Session", self.test_persistent_session)
            ]

            results = []

            for test_name, test_func in tests:
                print(f"\n🧪 Running {test_name}...")
                print("-" * 40)

                try:
                    result = await test_func()
                    results.append((test_name, result))

                    if result:
                        print(f"✅ {test_name}: PASSED")
                    else:
                        print(f"❌ {test_name}: FAILED")

                except Exception as e:
                    print(f"💥 {test_name}: CRASHED - {e}")
                    results.append((test_name, False))

            # Summary
            print("\n" + "=" * 60)
            print("📊 COMPLETE FLOW TEST SUMMARY:")

            passed = sum(1 for _, result in results if result)
            total = len(results)

            for test_name, result in results:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {test_name}: {status}")

            print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

            if passed == total:
                print("🎉 COMPLETE SUCCESS! All functionality working correctly.")
                print("\n📋 Summary of what was tested:")
                print("   ✅ User registration and authentication")
                print("   ✅ Profile creation with birth data")
                print("   ✅ Astrology chart generation")
                print("   ✅ AI-powered predictions (ChatGPT)")
                print("   ✅ Marriage compatibility analysis")
                print("   ✅ Persistent session management")
                print("   ✅ Data storage in Firestore")
                return True
            else:
                print("⚠️ Some tests failed. Check the implementation.")
                return False

        except Exception as e:
            print(f"💥 Complete flow test crashed: {e}")
            return False

    async def cleanup_test_data(self):
        """Clean up test data"""
        try:
            print("\n🧹 Cleaning up test data...")

            if self.test_user_id:
                # Delete test user data
                user_ref = self.db.collection('users').document(self.test_user_id)
                user_ref.delete()
                print(f"✅ Deleted test user: {self.test_user_id}")

                # Delete associated data
                await self._delete_collection(f'users/{self.test_user_id}/profiles')
                await self._delete_collection(f'users/{self.test_user_id}/partner_profiles')
                print("✅ Deleted user profiles and partners")

                # Delete predictions
                predictions_query = self.db.collection('predictions').where('user_id', '==', self.test_user_id)
                await self._delete_query_batch(predictions_query)
                print("✅ Deleted predictions")

                # Delete marriage matches
                matches_query = self.db.collection('marriage_matches').where('user_id', '==', self.test_user_id)
                await self._delete_query_batch(matches_query)
                print("✅ Deleted marriage matches")

                # Delete sessions
                sessions_query = self.db.collection('user_sessions').where('user_id', '==', self.test_user_id)
                await self._delete_query_batch(sessions_query)
                print("✅ Deleted user sessions")

            print("✅ Cleanup completed")
            return True

        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
            return False

    async def _delete_collection(self, collection_path: str):
        """Delete all documents in a collection"""
        try:
            collection_ref = self.db.collection(collection_path)
            docs = collection_ref.stream()

            for doc in docs:
                doc.reference.delete()

        except Exception as e:
            print(f"Failed to delete collection {collection_path}: {e}")

    async def _delete_query_batch(self, query):
        """Delete all documents matching a query"""
        try:
            docs = query.stream()

            for doc in docs:
                doc.reference.delete()

        except Exception as e:
            print(f"Failed to delete query batch: {e}")

async def main():
    """Main test function"""
    tester = CompleteFlowTester()

    try:
        # Run complete flow test
        success = await tester.test_complete_flow()

        # Clean up test data
        await tester.cleanup_test_data()

        # Exit with appropriate code
        exit_code = 0 if success else 1
        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        await tester.cleanup_test_data()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        await tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())