"""Reusable FastAPI dependencies: DB session, auth, role enforcement."""
from typing import Callable, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Decode the JWT bearer token and return the authenticated User ORM object.

    Raises:
        HTTPException 401: If the token is missing, invalid, or the user no
            longer exists in the database.
    """
    # Import here to avoid circular imports at module load time
    from app.models.user import User

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exc

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc

    return user


def require_role(*roles: str) -> Callable:
    """Return a FastAPI dependency that enforces role membership.

    Usage::

        @router.get("/admin-only")
        async def admin_only(user = Depends(require_role("admin"))):
            ...

    Args:
        *roles: One or more role strings the caller must possess.

    Returns:
        A dependency callable that raises HTTP 403 when the user's role is
        not in *roles*.
    """

    async def _check_role(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role(s): {', '.join(roles)}",
            )
        return current_user

    return _check_role
