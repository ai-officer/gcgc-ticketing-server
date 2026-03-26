"""Auth request/response schemas."""
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import BaseSchema


class LoginRequest(BaseModel):
    """Credentials sent by the client to obtain a JWT."""

    email: str
    password: str


class UserInToken(BaseSchema):
    """Minimal user info embedded in the login response."""

    id: int
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    is_on_duty: Optional[bool] = False


class TokenResponse(BaseModel):
    """JWT token payload returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
    user: UserInToken


class ChangePasswordRequest(BaseSchema):
    """Payload for the change-password endpoint."""

    current_password: str
    new_password: str
