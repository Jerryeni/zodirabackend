#!/usr/bin/env python3
"""
Profile Endpoint 403 Error Debugging Script

This script simulates the profile endpoint authorization issue by:
1. Creating a JWT token for a specific user
2. Testing different user_id scenarios that could cause 403 errors
3. Identifying the exact cause of the authorization failure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import create_access_token, verify_token
from app.core.dependencies import get_current_user
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import json

# Mock the HTTPBearer for testing
class MockCredentials:
    def __init__(self, token):
        self.credentials = token

def simulate_profile_endpoint_access():
    """Simulate the profile endpoint access pattern that causes 403 errors"""
    print("🔍 Profile Endpoint 403 Error Analysis")
    print("=" * 50)

    # Create a token for user "user123"
    token_user_id = "user123"
    token_data = {
        'sub': token_user_id,
        'email': 'user123@example.com',
        'phone': None,
        'auth_type': 'email'
    }

    try:
        # Create JWT token
        access_token = create_access_token(token_data)
        print(f"🔨 Created token for user: {token_user_id}")
        print(f"📋 Token: {access_token[:50]}...")

        # Verify the token works
        payload = verify_token(access_token)
        if payload:
            print(f"✅ Token verified for user: {payload.get('sub')}")

        # Test different scenarios that could cause 403 errors

        print("\n🔍 Testing authorization scenarios:")

        # Scenario 1: URL user_id matches token user_id (should work)
        print("\n1️⃣  Testing matching user_id...")
        try:
            mock_creds = MockCredentials(access_token)
            # Simulate get_current_user dependency
            token = mock_creds.credentials
            payload = verify_token(token)
            if payload and payload.get("sub") == token_user_id:
                print(f"✅ Authorization would succeed for user: {token_user_id}")
            else:
                print(f"❌ Authorization would fail for user: {token_user_id}")
        except Exception as e:
            print(f"❌ Error in scenario 1: {e}")

        # Scenario 2: URL user_id doesn't match token user_id (should cause 403)
        print("\n2️⃣  Testing mismatched user_id...")
        different_user_id = "user456"
        try:
            mock_creds = MockCredentials(access_token)
            token = mock_creds.credentials
            payload = verify_token(token)
            if payload and payload.get("sub") == different_user_id:
                print(f"✅ Authorization would succeed for user: {different_user_id}")
            else:
                print(f"❌ Authorization would fail for user: {different_user_id}")
                print(f"   💡 This is the expected 403 error scenario!")
        except Exception as e:
            print(f"❌ Error in scenario 2: {e}")

        # Scenario 3: Invalid token (should cause 401, not 403)
        print("\n3️⃣  Testing invalid token...")
        try:
            invalid_token = "invalid.jwt.token"
            mock_creds = MockCredentials(invalid_token)
            token = mock_creds.credentials
            payload = verify_token(token)
            if payload is None:
                print("✅ Invalid token correctly rejected (would be 401, not 403)")
            else:
                print("❌ Invalid token was accepted (security issue!)")
        except Exception as e:
            print(f"❌ Error in scenario 3: {e}")

        # Scenario 4: Missing token (should cause 401, not 403)
        print("\n4️⃣  Testing missing token...")
        try:
            mock_creds = MockCredentials("")
            token = mock_creds.credentials
            if not token:
                print("✅ Missing token correctly rejected (would be 401, not 403)")
        except Exception as e:
            print(f"❌ Error in scenario 4: {e}")

    except Exception as e:
        print(f"❌ Error in simulation: {e}")
        import traceback
        traceback.print_exc()

def analyze_profile_endpoints():
    """Analyze the profile endpoints to identify which ones could cause 403 errors"""
    print("\n🔍 Profile Endpoints Analysis")
    print("=" * 50)

    print("Based on the code analysis, these endpoints can return 403 errors:")
    print()

    endpoints_403 = [
        {
            "endpoint": "GET /{user_id}",
            "line": 541,
            "condition": "if current_user != user_id:",
            "description": "Getting user data - user_id must match token user_id"
        },
        {
            "endpoint": "GET /{user_id}/profile-status",
            "line": 572,
            "condition": "if current_user != user_id:",
            "description": "Getting user profile status - user_id must match token user_id"
        },
        {
            "endpoint": "POST /{user_id}",
            "line": 527,
            "condition": "if current_user != user_id:",
            "description": "Creating user - user_id must match token user_id"
        },
        {
            "endpoint": "GET /profiles/{profile_id}",
            "line": 737,
            "condition": "if data['user_id'] != current_user:",
            "description": "Getting profile - profile owner must match token user_id"
        },
        {
            "endpoint": "PUT /profiles/{profile_id}",
            "line": 782,
            "condition": "if data['user_id'] != current_user:",
            "description": "Updating profile - profile owner must match token user_id"
        },
        {
            "endpoint": "DELETE /profiles/{profile_id}",
            "line": 815,
            "condition": "if data['user_id'] != current_user:",
            "description": "Deleting profile - profile owner must match token user_id"
        }
    ]

    for endpoint in endpoints_403:
        print(f"🚫 {endpoint['endpoint']}")
        print(f"   📍 Line {endpoint['line']}")
        print(f"   🔒 Condition: {endpoint['condition']}")
        print(f"   📝 {endpoint['description']}")
        print()

def provide_solution():
    """Provide the solution for the 403 error"""
    print("\n💡 SOLUTION")
    print("=" * 50)

    print("The 403 error occurs when:")
    print("❌ The user_id in the URL path doesn't match the user_id in the JWT token")
    print()

    print("Common causes:")
    print("1. 🔄 Frontend sending wrong user_id in URL")
    print("2. 👤 User trying to access another user's data")
    print("3. 🆔 URL parameter mismatch with authenticated user")
    print("4. 🔧 API route expecting different user_id format")
    print()

    print("To fix this:")
    print("1. ✅ Verify the user_id in the JWT token matches the URL parameter")
    print("2. ✅ Check frontend code for correct user_id usage")
    print("3. ✅ Ensure proper authentication flow")
    print("4. ✅ Add logging to see the mismatch")
    print()

    print("Debug steps:")
    print("1. 🔍 Log the user_id from JWT token")
    print("2. 🔍 Log the user_id from URL parameter")
    print("3. 🔍 Compare them to identify the mismatch")
    print("4. 🔧 Fix the source of the mismatch")

if __name__ == "__main__":
    simulate_profile_endpoint_access()
    analyze_profile_endpoints()
    provide_solution()