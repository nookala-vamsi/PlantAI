"""
FastAPI dependencies — reusable injectable components for routes.
"""

from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.core.security import decode_token
from app.core.exceptions import TokenExpired, TokenBlacklisted, UserNotFound
from app.utils.redis_client import redis_client

# Bearer token extractor
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency that extracts and validates the JWT access token,
    checks the Redis blacklist, and returns the authenticated User.
    """
    token = credentials.credentials

    # 1. Decode the token
    try:
        payload = decode_token(token)
    except JWTError:
        raise TokenExpired()

    # 2. Verify it's an access token
    if payload.get("type") != "access":
        raise TokenExpired()

    # 3. Check Redis blacklist
    jti = payload.get("jti")
    if jti and await redis_client.is_blacklisted(jti):
        raise TokenBlacklisted()

    # 4. Get the user from database
    user_id = payload.get("sub")
    if not user_id:
        raise TokenExpired()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UserNotFound()

    return user
