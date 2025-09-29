from fastapi import HTTPException, status

class ZODIRAException(Exception):
    """Base exception for ZODIRA application"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthenticationError(ZODIRAException):
    """Authentication related errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)

class AuthorizationError(ZODIRAException):
    """Authorization related errors"""
    def __init__(self, message: str = "Not authorized to access this resource"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)

class NotFoundError(ZODIRAException):
    """Resource not found errors"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)

class ValidationError(ZODIRAException):
    """Data validation errors"""
    def __init__(self, message: str = "Invalid data provided"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)

class PaymentError(ZODIRAException):
    """Payment processing errors"""
    def __init__(self, message: str = "Payment processing failed"):
        super().__init__(message, status.HTTP_402_PAYMENT_REQUIRED)

class AstrologyCalculationError(ZODIRAException):
    """Astrology calculation errors"""
    def __init__(self, message: str = "Astrology calculation failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)

def handle_zodira_exception(exc: ZODIRAException) -> HTTPException:
    """Convert ZODIRA exceptions to FastAPI HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message
    )