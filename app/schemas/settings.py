"""SystemSettings request/response schemas."""
from typing import Optional

from app.schemas.common import BaseSchema


class BrandingSchema(BaseSchema):
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    company_name: Optional[str] = None


class ModulesSchema(BaseSchema):
    inventory: bool = True
    vendors: bool = True
    financials: bool = True
    preventive_maintenance: bool = True


class NotificationsSchema(BaseSchema):
    email_enabled: bool = False
    sms_enabled: bool = False
    slack_enabled: bool = False


class SystemSettingsResponse(BaseSchema):
    id: int
    branding: BrandingSchema
    modules: ModulesSchema
    notifications: NotificationsSchema


class SystemSettingsUpdate(BaseSchema):
    branding: Optional[BrandingSchema] = None
    modules: Optional[ModulesSchema] = None
    notifications: Optional[NotificationsSchema] = None
