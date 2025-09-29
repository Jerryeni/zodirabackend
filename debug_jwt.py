#!/usr/bin/env python3
"""
JWT Token Debugging Script

This script helps debug JWT token issues by:
1. Creating a test token
2. Attempting to verify it
3. Showing detailed error information
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, timezone
from app.config.settings import settings
from app.core.security import create_access_token, verify_token, TokenData
from jose import JWTError, jwt
import json
import logging

# Set up logging to see detailed errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_jwt_token_creation_and_verification():
    """Test JWT token creation and verification process"""
    print("🔍 JWT Token Debugging")
    print("=" * 50)

    # Test data
    test_user_id = "test_user_123"
    test_email = "test@example.com"

    token_data = {
        'sub': test_user_id,
        'email': test_email,
        'phone': None,
        'auth_type': 'email'
    }

    print(f"📝 Token Data: {json.dumps(token_data, indent=2)}")
    print(f"🔑 Secret Key: {settings.secret_key[:20]}...")
    print(f"🏷️  Issuer: {settings.app_name}")
    print(f"⚙️  Algorithm: {settings.algorithm}")
    print(f"⏰ Token Expiry: {settings.access_token_expire_minutes} minutes")

    try:
        # Create token
        print("\n🔨 Creating JWT token...")
        access_token = create_access_token(token_data)
        print(f"✅ Token created successfully: {access_token[:50]}...")

        # Decode token without verification to see structure
        print("\n🔍 Decoding token structure...")
        unverified_payload = jwt.get_unverified_header(access_token)
        print(f"📋 Header: {json.dumps(unverified_payload, indent=2)}")

        unverified_payload = jwt.decode(
            access_token,
            options={"verify_signature": False}
        )
        print(f"📋 Payload: {json.dumps(unverified_payload, indent=2)}")

        # Verify token
        print("\n🔐 Verifying JWT token...")
        verified_payload = verify_token(access_token)

        if verified_payload:
            print(f"✅ Token verified successfully: {json.dumps(verified_payload, indent=2)}")

            # Validate with TokenData model
            try:
                token_data_obj = TokenData(**verified_payload)
                print(f"✅ TokenData validation passed: {token_data_obj}")
            except Exception as e:
                print(f"❌ TokenData validation failed: {e}")
        else:
            print("❌ Token verification failed - returned None")

    except Exception as e:
        print(f"❌ Error during token processing: {e}")
        import traceback
        traceback.print_exc()

def test_token_verification_with_debug():
    """Test token verification with detailed debugging"""
    print("\n🔍 Detailed Token Verification Test")
    print("=" * 50)

    # Create a test token
    test_user_id = "debug_user_456"
    token_data = {
        'sub': test_user_id,
        'email': 'debug@test.com',
        'auth_type': 'test'
    }

    try:
        token = create_access_token(token_data)
        print(f"🔨 Created test token: {token[:30]}...")

        # Test the verify_token function step by step
        print("\n🔍 Step-by-step verification:")

        # Step 1: Check if token is blacklisted
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        print(f"📋 Token hash: {token_hash}")

        # Step 2: Decode token
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
                options={"verify_exp": True, "verify_iat": True}
            )
            print(f"✅ Token decoded successfully: {json.dumps(payload, indent=2)}")

            # Step 3: Validate issuer
            if payload.get('iss') != settings.app_name:
                print(f"❌ Issuer mismatch: {payload.get('iss')} != {settings.app_name}")
            else:
                print(f"✅ Issuer validation passed: {payload.get('iss')}")

            # Step 4: Validate with TokenData model
            try:
                token_data_obj = TokenData(**payload)
                print(f"✅ TokenData validation passed: {token_data_obj}")
            except Exception as e:
                print(f"❌ TokenData validation failed: {e}")

        except JWTError as e:
            print(f"❌ JWT decoding failed: {e}")
        except Exception as e:
            print(f"❌ Token verification error: {e}")

    except Exception as e:
        print(f"❌ Error in verification test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_jwt_token_creation_and_verification()
    test_token_verification_with_debug()