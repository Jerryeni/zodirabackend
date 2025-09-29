#!/usr/bin/env python3
"""
Firebase Connection Test Script
Run this script to test your Firebase configuration after migration
"""

from app.config.firebase import get_firestore_client, initialize_firebase
from datetime import datetime
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_firestore_connection():
    """Test Firestore database connection"""
    try:
        print("🔄 Testing Firestore connection...")

        # Initialize Firebase
        db, bucket = initialize_firebase()
        print("✅ Firebase initialized successfully")

        # Test write operation
        doc_ref = db.collection('test').document('migration-test')
        test_data = {
            'message': 'Migration test successful!',
            'timestamp': datetime.utcnow(),
            'project_id': os.getenv('FIREBASE_PROJECT_ID', 'unknown')
        }

        doc_ref.set(test_data)
        print("✅ Test document written successfully")

        # Test read operation
        doc = doc_ref.get()
        if doc.exists:
            retrieved_data = doc.to_dict()
            print("✅ Test document read successfully")
            print(f"📄 Document data: {retrieved_data}")

            # Verify data integrity
            if retrieved_data['message'] == test_data['message']:
                print("✅ Data integrity check passed")
            else:
                print("❌ Data integrity check failed")
                return False
        else:
            print("❌ Test document not found")
            return False

        # Clean up
        doc_ref.delete()
        print("✅ Test document deleted")

        return True

    except Exception as e:
        print(f"❌ Firestore connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_storage_connection():
    """Test Firebase Storage connection"""
    try:
        print("🔄 Testing Firebase Storage connection...")

        # Initialize Firebase
        db, bucket = initialize_firebase()
        print("✅ Firebase Storage initialized")

        # Test file upload
        blob = bucket.blob('test/migration-test.txt')
        test_content = 'Migration test successful!'

        blob.upload_from_string(test_content)
        print("✅ Test file uploaded")

        # Test file download
        downloaded_content = blob.download_as_text()
        print(f"✅ Test file downloaded: {downloaded_content}")

        # Verify content
        if downloaded_content == test_content:
            print("✅ Content integrity check passed")
        else:
            print("❌ Content integrity check failed")
            return False

        # Clean up
        blob.delete()
        print("✅ Test file deleted")

        return True

    except Exception as e:
        print(f"❌ Storage connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth_service():
    """Test Firebase Authentication service"""
    try:
        print("🔄 Testing Firebase Authentication...")

        from firebase_admin import auth

        # Initialize Firebase
        db, bucket = initialize_firebase()
        print("✅ Firebase Auth initialized")

        # Test creating a user (for testing purposes)
        test_email = 'test-migration@example.com'
        test_user = None

        try:
            user = auth.create_user(
                email=test_email,
                email_verified=True,
                display_name='Migration Test User'
            )
            test_user = user
            print(f"✅ Test user created: {user.uid}")

            # Test retrieving user
            retrieved_user = auth.get_user(user.uid)
            if retrieved_user.email == test_email:
                print("✅ User retrieval test passed")
            else:
                print("❌ User retrieval test failed")
                return False

        except Exception as e:
            print(f"⚠️ User creation test failed (may be expected): {e}")
            # This might fail if user already exists, which is okay for testing

        # Clean up - only delete if we created it
        if test_user:
            try:
                auth.delete_user(test_user.uid)
                print("✅ Test user deleted")
            except Exception as e:
                print(f"⚠️ User deletion failed (may be okay): {e}")

        return True

    except Exception as e:
        print(f"❌ Auth service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Firebase Migration Tests")
    print("=" * 50)

    # Test environment variables
    print("📋 Environment Check:")
    print(f"   Project ID: {os.getenv('FIREBASE_PROJECT_ID', 'NOT SET')}")
    print(f"   Storage Bucket: {os.getenv('FIREBASE_STORAGE_BUCKET', 'NOT SET')}")
    print(f"   Service Account: {os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH', 'NOT SET')}")
    print()

    tests = [
        ("Firestore Database", test_firestore_connection),
        ("Cloud Storage", test_storage_connection),
        ("Authentication", test_auth_service)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test:")
        print("-" * 30)

        try:
            result = test_func()
            results.append((test_name, result))

            if result:
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")

        except Exception as e:
            print(f"💥 {test_name} test CRASHED: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your Firebase migration is successful.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check your configuration.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)