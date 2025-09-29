"""
Comprehensive tests for the unified authentication system

This test suite covers:
- Email and phone authentication flows
- OTP generation and verification
- Google OAuth integration
- Session management and security
- Rate limiting and error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json

from fastapi.testclient import TestClient
from app.main import app
from app.services.unified_auth_service import UnifiedAuthService, AuthType, AuthStatus
from app.core.exceptions import AuthenticationError, ValidationError

client = TestClient(app)

class TestUnifiedAuthService:
    """Test cases for UnifiedAuthService"""
    
    @pytest.fixture
    def auth_service(self):
        """Create auth service instance for testing"""
        service = UnifiedAuthService()
        service.redis_client = Mock()  # Mock Redis
        service.db = Mock()  # Mock Firestore
        return service
    
    @pytest.mark.asyncio
    async def test_determine_auth_type_email(self, auth_service):
        """Test email authentication type detection"""
        auth_type = auth_service._determine_auth_type("test@example.com")
        assert auth_type == AuthType.EMAIL
    
    @pytest.mark.asyncio
    async def test_determine_auth_type_phone(self, auth_service):
        """Test phone authentication type detection"""
        auth_type = auth_service._determine_auth_type("+1234567890")
        assert auth_type == AuthType.PHONE
    
    @pytest.mark.asyncio
    async def test_determine_auth_type_invalid(self, auth_service):
        """Test invalid identifier handling"""
        with pytest.raises(ValidationError):
            auth_service._determine_auth_type("invalid-identifier")
    
    @pytest.mark.asyncio
    @patch('app.services.unified_auth_service.httpx.AsyncClient')
    async def test_send_sms_otp_success(self, mock_client, auth_service):
        """Test successful SMS OTP sending"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "success"
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        # Should not raise exception
        await auth_service._send_sms_otp("+1234567890", "123456")
    
    @pytest.mark.asyncio
    @patch('app.services.unified_auth_service.httpx.AsyncClient')
    async def test_send_sms_otp_failure(self, mock_client, auth_service):
        """Test SMS OTP sending failure"""
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status_code = 400
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        with pytest.raises(AuthenticationError):
            await auth_service._send_sms_otp("+1234567890", "123456")
    
    @pytest.mark.asyncio
    async def test_initiate_auth_email(self, auth_service):
        """Test email authentication initiation"""
        with patch.object(auth_service, '_send_email_otp') as mock_send_email:
            mock_send_email.return_value = None
            
            result = await auth_service.initiate_auth("test@example.com")
            
            assert result['auth_type'] == AuthType.EMAIL.value
            assert result['status'] == AuthStatus.OTP_SENT.value
            assert 'session_id' in result
            mock_send_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initiate_auth_phone(self, auth_service):
        """Test phone authentication initiation"""
        with patch.object(auth_service, '_send_sms_otp') as mock_send_sms:
            mock_send_sms.return_value = None
            
            result = await auth_service.initiate_auth("+1234567890")
            
            assert result['auth_type'] == AuthType.PHONE.value
            assert result['status'] == AuthStatus.OTP_SENT.value
            assert 'session_id' in result
            mock_send_sms.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_otp_success(self, auth_service):
        """Test successful OTP verification"""
        session_id = "test_session_123"
        otp_code = "123456"
        
        # Mock session data
        session_data = {
            'identifier': 'test@example.com',
            'auth_type': AuthType.EMAIL.value,
            'otp_code': otp_code,
            'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            'attempts': 0,
            'max_attempts': 3
        }
        
        with patch.object(auth_service, '_get_session') as mock_get_session, \
             patch.object(auth_service, '_get_or_create_user') as mock_get_user, \
             patch.object(auth_service, '_determine_next_step') as mock_next_step, \
             patch.object(auth_service, '_store_session') as mock_store_session:
            
            mock_get_session.return_value = session_data
            mock_get_user.return_value = {
                'uid': 'user123',
                'email': 'test@example.com',
                'is_new_user': False,
                'profile_complete': True
            }
            mock_next_step.return_value = 'dashboard'
            
            result = await auth_service.verify_otp(session_id, otp_code)
            
            assert result['status'] == AuthStatus.AUTHENTICATED.value
            assert result['user_id'] == 'user123'
            assert 'access_token' in result
    
    @pytest.mark.asyncio
    async def test_verify_otp_invalid_code(self, auth_service):
        """Test OTP verification with invalid code"""
        session_id = "test_session_123"
        otp_code = "123456"
        wrong_code = "654321"
        
        session_data = {
            'identifier': 'test@example.com',
            'auth_type': AuthType.EMAIL.value,
            'otp_code': otp_code,
            'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            'attempts': 0,
            'max_attempts': 3
        }
        
        with patch.object(auth_service, '_get_session') as mock_get_session, \
             patch.object(auth_service, '_store_session') as mock_store_session:
            
            mock_get_session.return_value = session_data
            
            with pytest.raises(AuthenticationError, match="Invalid OTP"):
                await auth_service.verify_otp(session_id, wrong_code)
    
    @pytest.mark.asyncio
    async def test_verify_otp_expired(self, auth_service):
        """Test OTP verification with expired session"""
        session_id = "test_session_123"
        otp_code = "123456"
        
        session_data = {
            'identifier': 'test@example.com',
            'auth_type': AuthType.EMAIL.value,
            'otp_code': otp_code,
            'expires_at': (datetime.utcnow() - timedelta(minutes=1)).isoformat(),  # Expired
            'attempts': 0,
            'max_attempts': 3
        }
        
        with patch.object(auth_service, '_get_session') as mock_get_session, \
             patch.object(auth_service, '_delete_session') as mock_delete_session:
            
            mock_get_session.return_value = session_data
            
            with pytest.raises(AuthenticationError, match="OTP has expired"):
                await auth_service.verify_otp(session_id, otp_code)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, auth_service):
        """Test rate limiting functionality"""
        identifier = "test@example.com"
        
        # Mock Redis to return high attempt count
        auth_service.redis_client.get.return_value = b'6'  # Above limit of 5
        
        with pytest.raises(AuthenticationError, match="Too many authentication attempts"):
            await auth_service._check_rate_limit(identifier)

class TestUnifiedAuthAPI:
    """Test cases for unified authentication API endpoints"""
    
    def test_initiate_auth_email_valid(self):
        """Test authentication initiation with valid email"""
        with patch('app.services.unified_auth_service.unified_auth_service.initiate_auth') as mock_initiate:
            mock_initiate.return_value = {
                'session_id': 'session123',
                'auth_type': 'email',
                'status': 'otp_sent',
                'message': 'OTP sent to your email',
                'expires_in': 300,
                'next_step': 'verify_otp'
            }
            
            response = client.post(
                "/api/v1/auth/initiate",
                json={"identifier": "test@example.com"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['auth_type'] == 'email'
            assert data['status'] == 'otp_sent'
    
    def test_initiate_auth_phone_valid(self):
        """Test authentication initiation with valid phone"""
        with patch('app.services.unified_auth_service.unified_auth_service.initiate_auth') as mock_initiate:
            mock_initiate.return_value = {
                'session_id': 'session123',
                'auth_type': 'phone',
                'status': 'otp_sent',
                'message': 'OTP sent to your phone',
                'expires_in': 300,
                'next_step': 'verify_otp'
            }
            
            response = client.post(
                "/api/v1/auth/initiate",
                json={"identifier": "+1234567890"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['auth_type'] == 'phone'
            assert data['status'] == 'otp_sent'
    
    def test_initiate_auth_invalid_identifier(self):
        """Test authentication initiation with invalid identifier"""
        response = client.post(
            "/api/v1/auth/initiate",
            json={"identifier": "invalid-identifier"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_verify_otp_success(self):
        """Test successful OTP verification"""
        with patch('app.services.unified_auth_service.unified_auth_service.verify_otp') as mock_verify:
            mock_verify.return_value = {
                'session_id': 'session123',
                'access_token': 'jwt_token_here',
                'user_id': 'user123',
                'status': 'authenticated',
                'is_new_user': False,
                'next_step': 'dashboard',
                'user_data': {
                    'uid': 'user123',
                    'email': 'test@example.com',
                    'profile_complete': True
                }
            }
            
            response = client.post(
                "/api/v1/auth/verify-otp",
                json={
                    "session_id": "session123",
                    "otp_code": "123456"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'authenticated'
            assert 'access_token' in data
    
    def test_verify_otp_invalid_format(self):
        """Test OTP verification with invalid OTP format"""
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={
                "session_id": "session123",
                "otp_code": "12345"  # Too short
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_google_oauth_success(self):
        """Test successful Google OAuth login"""
        with patch('app.services.unified_auth_service.unified_auth_service.google_oauth_login') as mock_oauth:
            mock_oauth.return_value = {
                'access_token': 'jwt_token_here',
                'user_id': 'user123',
                'status': 'authenticated',
                'is_new_user': True,
                'next_step': 'complete_profile',
                'user_data': {
                    'uid': 'user123',
                    'email': 'test@gmail.com',
                    'display_name': 'Test User',
                    'profile_complete': False
                }
            }
            
            response = client.post(
                "/api/v1/auth/google-oauth",
                json={"id_token": "valid_google_id_token_here"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'authenticated'
            assert data['is_new_user'] == True
    
    def test_auth_health_check(self):
        """Test authentication service health check"""
        response = client.get("/api/v1/auth/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'redis' in data
        assert 'firebase' in data

class TestAuthenticationSecurity:
    """Test cases for authentication security features"""
    
    @pytest.mark.asyncio
    async def test_session_storage_redis(self):
        """Test session storage with Redis"""
        service = UnifiedAuthService()
        service.redis_client = Mock()
        
        session_id = "test_session"
        session_data = {"test": "data"}
        
        await service._store_session(session_id, session_data)
        
        service.redis_client.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_retrieval_redis(self):
        """Test session retrieval with Redis"""
        service = UnifiedAuthService()
        service.redis_client = Mock()
        service.redis_client.get.return_value = json.dumps({"test": "data"})
        
        session_id = "test_session"
        result = await service._get_session(session_id)
        
        assert result == {"test": "data"}
        service.redis_client.get.assert_called_once_with(f"auth_session:{session_id}")
    
    @pytest.mark.asyncio
    async def test_session_deletion_redis(self):
        """Test session deletion with Redis"""
        service = UnifiedAuthService()
        service.redis_client = Mock()
        
        session_id = "test_session"
        await service._delete_session(session_id)
        
        service.redis_client.delete.assert_called_once_with(f"auth_session:{session_id}")

class TestAuthenticationIntegration:
    """Integration tests for authentication flows"""
    
    @pytest.mark.asyncio
    async def test_complete_email_auth_flow(self):
        """Test complete email authentication flow"""
        service = UnifiedAuthService()
        service.redis_client = Mock()
        service.db = Mock()
        
        # Mock all external dependencies
        with patch.object(service, '_send_email_otp') as mock_email, \
             patch.object(service, '_get_or_create_user') as mock_user, \
             patch.object(service, '_determine_next_step') as mock_next_step:
            
            mock_email.return_value = None
            mock_user.return_value = {
                'uid': 'user123',
                'email': 'test@example.com',
                'is_new_user': False,
                'profile_complete': True
            }
            mock_next_step.return_value = 'dashboard'
            
            # Step 1: Initiate authentication
            result1 = await service.initiate_auth("test@example.com")
            session_id = result1['session_id']
            
            # Step 2: Verify OTP (mock session data)
            with patch.object(service, '_get_session') as mock_get_session:
                mock_get_session.return_value = {
                    'identifier': 'test@example.com',
                    'auth_type': 'email',
                    'otp_code': '123456',
                    'expires_at': (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
                    'attempts': 0,
                    'max_attempts': 3
                }
                
                result2 = await service.verify_otp(session_id, '123456')
                
                assert result2['status'] == 'authenticated'
                assert 'access_token' in result2

# Fixtures and utilities
@pytest.fixture
def mock_redis():
    """Mock Redis client for testing"""
    return Mock()

@pytest.fixture
def mock_firestore():
    """Mock Firestore client for testing"""
    return Mock()

# Run tests
if __name__ == "__main__":
    pytest.main([__file__])