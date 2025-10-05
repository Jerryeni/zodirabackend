from pydantic_settings import BaseSettings
from decouple import config
from typing import List
import secrets
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Firebase Configuration
    firebase_project_id: str = config('FIREBASE_PROJECT_ID', default='your-firebase-project-id')
    firebase_storage_bucket: str = config('FIREBASE_STORAGE_BUCKET', default='your-firebase-project-id.appspot.com')

    # Application Settings
    app_name: str = "ZODIRA Backend"
    app_version: str = "1.0.0"
    debug: bool = config('APP_DEBUG', default=False, cast=bool)  # Changed from DEBUG to APP_DEBUG
    environment: str = config('ENVIRONMENT', default='development')

    # Security Configuration
    secret_key: str = config('SECRET_KEY', default='dev-secret-key-change-in-production-min-32-chars')
    algorithm: str = "HS256"
    access_token_expire_minutes: int = config('ACCESS_TOKEN_EXPIRE_MINUTES', default=180, cast=int)
    
    # CORS Configuration - Accept all origins for development
    allowed_origins: List[str] = config(
        'ALLOWED_ORIGINS',
        default='*',
        cast=lambda v: [s.strip() for s in v.split(',')] if v != '*' else ['*']
    )
    
    # Rate Limiting
    rate_limit_requests: int = config('RATE_LIMIT_REQUESTS', default=100, cast=int)
    rate_limit_window: int = config('RATE_LIMIT_WINDOW', default=60, cast=int)
    
    # SMS Configuration (for phone verification)
    sms_provider: str = config('SMS_PROVIDER', default='mydreams')
    
    # MyDreams Technology SMS API Configuration
    mydreams_api_url: str = config('MYDREAMS_API_URL', default='http://app.mydreamstechnology.in/vb/apikey.php')
    mydreams_api_key: str = config('MYDREAMS_API_KEY', default='zbAG4xSPKhwqPCI3')
    mydreams_sender_id: str = config('MYDREAMS_SENDER_ID', default='MYDTEH')
    
    # Google OAuth Configuration
    google_client_id: str = config('GOOGLE_CLIENT_ID', default='')
    google_client_secret: str = config('GOOGLE_CLIENT_SECRET', default='')
    redirect_uri: str = config('REDIRECT_URI', default='')
    frontend_url: str = config('FRONTEND_URL', default='*')

    # Twilio Configuration (fallback)
    twilio_account_sid: str = config('TWILIO_ACCOUNT_SID', default='')
    twilio_auth_token: str = config('TWILIO_AUTH_TOKEN', default='')
    twilio_phone_number: str = config('TWILIO_PHONE_NUMBER', default='')
    
    # Application Contact Information
    zodira_support_email: str = config('ZODIRA_SUPPORT_EMAIL', default='enijerry0@gmail.com')

    # Astrology API Configuration
    free_astrology_api_key: str = config('FREE_ASTRO_API_KEY', default='')

    # OpenAI ChatGPT Configuration
    openai_api_key: str = config('OPENAI_API_KEY', default='')

    # OpenAI Model Configuration (Modern Best Practices)
    openai_model: str = config('OPENAI_MODEL', default='gpt-3.5-turbo')
    openai_max_tokens: int = config('OPENAI_MAX_TOKENS', default=2000, cast=int)
    openai_temperature: float = config('OPENAI_TEMPERATURE', default=0.3, cast=float)
    openai_timeout: int = config('OPENAI_TIMEOUT', default=30, cast=int)
    openai_max_retries: int = config('OPENAI_MAX_RETRIES', default=3, cast=int)
    openai_rate_limit_per_minute: int = config('OPENAI_RATE_LIMIT_PER_MINUTE', default=50, cast=int)

    # Redis removed: using Firestore for sessions and rate limits
    
    # Logging Configuration
    log_level: str = config('LOG_LEVEL', default='INFO')
    log_format: str = config('LOG_FORMAT', default='json')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()
    
    def _validate_security_settings(self):
        """Validate critical security settings"""
        # Generate secure secret key if using default
        if not self.secret_key or self.secret_key in ['your-secret-key-here', 'dev-secret-key-change-in-production-min-32-chars']:
            if self.environment == 'production':
                logger.critical("SECURITY ALERT: Default SECRET_KEY used in production!")
                raise ValueError("SECRET_KEY must be set to a secure value in production environment")
            else:
                # Generate secure key for development
                self.secret_key = secrets.token_urlsafe(32)
                logger.warning(f"Generated secure SECRET_KEY for {self.environment} environment")
        
        # Validate Firebase configuration
        if self.firebase_project_id == 'your-firebase-project-id':
            logger.warning("Firebase project ID not configured - using default")
        
        # Validate payment configuration (temporarily disabled)
        # if self.razorpay_key_id == 'your_razorpay_key_id':
        #     logger.warning("Razorpay configuration not set - payments will not work")
        
        # Validate CORS origins
        if '*' in self.allowed_origins:
            logger.info("Wildcard CORS origin enabled for all environments")
        
        # Google OAuth optional: keep app running even if not configured
        if not self.google_client_id or not self.google_client_secret or not self.redirect_uri:
            logger.info("Google OAuth not fully configured; endpoints relying on Google OAuth will be inactive until GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/REDIRECT_URI are set")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

# Global settings instance
settings = Settings()