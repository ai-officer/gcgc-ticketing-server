"""User request/response schemas."""
from typing import Optional

from pydantic import EmailStr

from app.schemas.common import BaseSchema


class UserBase(BaseSchema):
    name: str
    email: str
    role: str
    avatar: Optional[str] = None
    is_on_duty: Optional[bool] = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseSchema):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    avatar: Optional[str] = None
    is_on_duty: Optional[bool] = None


class UserResponse(UserBase):
    id: int

    model_config = UserBase.model_config


class DutyToggleRequest(BaseSchema):
    is_on_duty: bool
