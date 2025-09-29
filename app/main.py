import logging
import sys
from fastapi import FastAPI, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import generate_latest

# Import from new structure
from app.config.firebase import initialize_firebase
from app.config.settings import settings
from app.api.v1.user_management import router as user_management_router
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.astrology import router as astrology_router
from app.api.v1.enhanced_astrology import router as enhanced_astrology_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Security validation will be handled by settings validation

# Initialize Firebase on startup
initialize_firebase()

app = FastAPI(
    title=settings.app_name,
    description="Cosmic Predictions API with Vedic Astrology",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware with Flutter-optimized configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Accept-Language",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=[
        "X-Total-Count",
        "X-Request-ID",
        "Content-Length",
        "Content-Range"
    ],
    max_age=86400,  # Cache preflight response for 24 hours
)

# Log CORS configuration for security audit
logger.info(f"CORS configured for origins: {settings.allowed_origins}")
logger.info(f"CORS configured successfully for {settings.environment} environment")

# Include API routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_management_router, prefix="/api/v1/auth", tags=["User Management"])
app.include_router(astrology_router, prefix="/api/v1/astrology", tags=["Astrology"])
app.include_router(enhanced_astrology_router, prefix="/api/v1/enhanced", tags=["Enhanced Astrology"])

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)