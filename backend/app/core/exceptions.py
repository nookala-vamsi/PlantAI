"""
Custom exception classes and standardized error response format.
"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base exception with standardized error format."""

    def __init__(self, status_code: int, error_code: str, message: str, details: str = None):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(
            status_code=status_code,
            detail={
                "status": "error",
                "error_code": error_code,
                "message": message,
                "details": details,
            },
        )


# ── Auth Exceptions ──

class InvalidCredentials(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
        )


class TokenExpired(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTH_EXPIRED",
            message="Your session has expired. Please login again.",
        )


class TokenBlacklisted(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="TOKEN_REVOKED",
            message="This token has been revoked. Please login again.",
        )


class UserAlreadyExists(AppException):
    def __init__(self, field: str = "email"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="USER_EXISTS",
            message=f"A user with this {field} already exists.",
        )


class UserNotFound(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="USER_NOT_FOUND",
            message="User not found.",
        )


# ── Prediction Exceptions ──

class InvalidImage(AppException):
    def __init__(self, reason: str = "Only JPEG and PNG images are supported."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_IMAGE",
            message=reason,
        )


class ImageTooLarge(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="IMAGE_TOO_LARGE",
            message="Image must be under 10 MB.",
        )


class InvalidCrop(AppException):
    def __init__(self, crop: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_CROP",
            message=f"'{crop}' is not a supported crop.",
        )


class RateLimitExceeded(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT",
            message="Too many requests. Please wait a moment.",
        )


class PredictionFailed(AppException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="PREDICTION_FAILED",
            message="Unable to process this image. Please try again.",
        )
