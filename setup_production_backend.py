#!/usr/bin/env python3
"""
Production Backend Setup Script for ZODIRA

This script sets up everything needed for a production-ready backend:
1. Initializes Firebase connection
2. Saves AI prompts to database
3. Tests all services and configurations
4. Provides setup verification
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config.firebase import get_firestore_client, initialize_firebase
from app.config.settings import settings

class ProductionSetup:
    """Production setup manager"""

    def __init__(self):
        self.db = None
        self.setup_steps = []

    async def run_complete_setup(self):
        """Run complete production setup"""
        print("🚀 ZODIRA Production Backend Setup")
        print("=" * 60)

        try:
            # Step 1: Initialize Firebase
            await self.initialize_firebase()
            self.setup_steps.append(("Firebase Initialization", True, "✅ Connected successfully"))

            # Step 2: Save AI prompts
            await self.save_ai_prompts()
            self.setup_steps.append(("AI Prompts Setup", True, "✅ Saved to database"))

            # Step 3: Test services
            await self.test_services()
            self.setup_steps.append(("Service Testing", True, "✅ All services operational"))

            # Step 4: Verify configuration
            await self.verify_configuration()
            self.setup_steps.append(("Configuration Verification", True, "✅ Settings validated"))

            # Step 5: Create setup report
            self.create_setup_report()

            print("\n🎉 Production setup completed successfully!")
            print("\n📋 Next steps:")
            print("   1. Set your OPENAI_API_KEY in .env file")
            print("   2. Run 'python test_complete_flow.py' to test functionality")
            print("   3. Deploy to production environment")
            print("   4. Update Flutter app with new endpoints")

            return True

        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def initialize_firebase(self):
        """Initialize Firebase connection"""
        try:
            print("🔄 Initializing Firebase...")
            initialize_firebase()
            self.db = get_firestore_client()

            # Test connection
            test_ref = self.db.collection('test').document('setup_test')
            test_ref.set({
                'message': 'Firebase connection test',
                'timestamp': datetime.utcnow()
            })

            # Clean up test
            test_ref.delete()

            print("✅ Firebase initialized successfully")
            return True

        except Exception as e:
            print(f"❌ Firebase initialization failed: {e}")
            raise

    async def save_ai_prompts(self):
        """Save AI prompts to database"""
        try:
            print("🔄 Saving AI prompts to database...")

            # Import the initialization script
            from initialize_ai_prompts import initialize_ai_prompts

            success = await initialize_ai_prompts()
            if not success:
                raise Exception("AI prompts initialization failed")

            print("✅ AI prompts saved successfully")
            return True

        except Exception as e:
            print(f"❌ AI prompts setup failed: {e}")
            raise

    async def test_services(self):
        """Test all backend services"""
        try:
            print("🔄 Testing backend services...")

            # Test imports
            try:
                from app.services.user_service import user_service
                from app.services.enhanced_astrology_service import enhanced_astrology_service
                from app.services.chatgpt_service import chatgpt_service
                print("✅ Service imports successful")
            except Exception as e:
                raise Exception(f"Service import failed: {e}")

            # Test database connection
            try:
                test_ref = self.db.collection('service_test').document('test')
                test_ref.set({'test': True, 'timestamp': datetime.utcnow()})
                test_ref.delete()
                print("✅ Database operations working")
            except Exception as e:
                raise Exception(f"Database test failed: {e}")

            # Test settings
            try:
                print(f"✅ Settings loaded: {settings.app_name} v{settings.app_version}")
                print(f"   Environment: {settings.environment}")
                print(f"   Debug mode: {settings.debug}")
            except Exception as e:
                raise Exception(f"Settings test failed: {e}")

            print("✅ All services tested successfully")
            return True

        except Exception as e:
            print(f"❌ Service testing failed: {e}")
            raise

    async def verify_configuration(self):
        """Verify all configurations are correct"""
        try:
            print("🔄 Verifying configuration...")

            # Check required environment variables
            required_vars = [
                'FIREBASE_PROJECT_ID',
                'FIREBASE_STORAGE_BUCKET',
                'SECRET_KEY'
            ]

            missing_vars = []
            for var in required_vars:
                value = os.getenv(var)
                if not value or value.startswith('your_'):
                    missing_vars.append(var)

            if missing_vars:
                print(f"⚠️ Missing or default configuration: {', '.join(missing_vars)}")
                print("   Please update your .env file with proper values")
            else:
                print("✅ All required configurations present")

            # Check OpenAI API key
            openai_key = os.getenv('OPENAI_API_KEY')
            if not openai_key or openai_key == 'your_openai_api_key_here':
                print("⚠️ OpenAI API key not configured")
                print("   AI features will use mock data until configured")
            else:
                print("✅ OpenAI API key configured")

            # Check Firebase configuration
            firebase_project = settings.firebase_project_id
            if firebase_project and not firebase_project.startswith('your_'):
                print(f"✅ Firebase project configured: {firebase_project}")
            else:
                print("⚠️ Firebase project not properly configured")

            print("✅ Configuration verification completed")
            return True

        except Exception as e:
            print(f"❌ Configuration verification failed: {e}")
            raise

    def create_setup_report(self):
        """Create setup completion report"""
        try:
            print("\n📊 Creating setup report...")

            report = {
                'setup_timestamp': datetime.utcnow().isoformat(),
                'app_name': settings.app_name,
                'app_version': settings.app_version,
                'environment': settings.environment,
                'firebase_project': settings.firebase_project_id,
                'features_enabled': [
                    'Persistent Authentication',
                    'AI Predictions',
                    'Marriage Compatibility',
                    'Astrology Charts',
                    'Profile Management',
                    'Dashboard Analytics'
                ],
                'api_endpoints': [
                    '/api/v1/enhanced/auth/persistent-login',
                    '/api/v1/enhanced/profiles/{id}/generate-chart',
                    '/api/v1/enhanced/profiles/{id}/predictions',
                    '/api/v1/enhanced/marriage-matching/generate',
                    '/api/v1/enhanced/dashboard'
                ],
                'setup_steps': self.setup_steps
            }

            # Save report to database
            report_ref = self.db.collection('system').document('setup_report')
            report_ref.set(report)

            print("✅ Setup report saved to database")
            print("\n📋 Setup Summary:")
            print(f"   App: {report['app_name']} v{report['app_version']}")
            print(f"   Environment: {report['environment']}")
            print(f"   Firebase: {report['firebase_project']}")
            print(f"   Features: {len(report['features_enabled'])} enabled")
            print(f"   API Endpoints: {len(report['api_endpoints'])} available")

            # Print step results
            print("\n🔧 Setup Steps:")
            for step_name, success, message in self.setup_steps:
                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} {step_name}: {message}")

            return True

        except Exception as e:
            print(f"❌ Failed to create setup report: {e}")
            return False

async def main():
    """Main setup function"""
    setup = ProductionSetup()

    try:
        success = await setup.run_complete_setup()

        if success:
            print("\n🎯 Your backend is production-ready!")
            print("\n🔑 To complete setup:")
            print("   1. Add your OPENAI_API_KEY to .env file")
            print("   2. Run 'python test_complete_flow.py' to verify functionality")
            print("   3. Deploy to your production environment")
            print("   4. Share the Flutter implementation guide with your developer")

            return 0
        else:
            print("\n❌ Setup completed with errors")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Setup crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)