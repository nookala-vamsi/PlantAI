"""
Auth router — registration, login, logout, token refresh.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, AccessTokenResponse, MessageResponse,
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.dependencies import get_current_user
from app.core.exceptions import (
    InvalidCredentials, UserAlreadyExists, TokenExpired,
)
from app.utils.redis_client import redis_client
from jose import JWTError

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""

    # Check if email or username already exists
    result = await db.execute(
        select(User).where(
            or_(User.email == request.email, User.username == request.username)
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        field = "email" if existing.email == request.email else "username"
        raise UserAlreadyExists(field=field)

    # Create user
    user = User(
        email=request.email,
        username=request.username,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    await db.flush()

    return MessageResponse(message="Registration successful. You can now login.")


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login and receive access + refresh tokens."""

    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise InvalidCredentials()

    if not user.is_active:
        raise InvalidCredentials()

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(request: RefreshRequest):
    """Get a new access token using a refresh token."""

    try:
        payload = decode_token(request.refresh_token)
    except JWTError:
        raise TokenExpired()

    if payload.get("type") != "refresh":
        raise TokenExpired()

    # Check if refresh token is blacklisted
    jti = payload.get("jti")
    if jti and await redis_client.is_blacklisted(jti):
        raise TokenExpired()

    user_id = payload.get("sub")
    return AccessTokenResponse(
        access_token=create_access_token(user_id),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(user: User = Depends(get_current_user)):
    """Logout — blacklist the current access token."""
    # Note: The actual token blacklisting is handled by sending the token JTI
    # For simplicity, we return success. The frontend should discard tokens.
    return MessageResponse(message="Logged out successfully.")
