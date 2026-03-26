"""System Settings routes — singleton row management."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models.system_settings import SystemSettings
from app.models.user import User
from app.schemas.settings import BrandingSchema, ModulesSchema, NotificationsSchema, SystemSettingsResponse, SystemSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _orm_to_response(s: SystemSettings) -> SystemSettingsResponse:
    return SystemSettingsResponse(
        id=s.id,
        branding=BrandingSchema(
            logo_url=s.logo_url,
            primary_color=s.primary_color,
            company_name=s.company_name,
        ),
        modules=ModulesSchema(
            inventory=s.module_inventory,
            vendors=s.module_vendors,
            financials=s.module_financials,
            preventive_maintenance=s.module_preventive_maintenance,
        ),
        notifications=NotificationsSchema(
            email_enabled=s.notification_email_enabled,
            sms_enabled=s.notification_sms_enabled,
            slack_enabled=s.notification_slack_enabled,
        ),
    )


async def _get_or_create_settings(db: AsyncSession) -> SystemSettings:
    """Fetch the singleton settings row, creating it with defaults if absent."""
    result = await db.execute(select(SystemSettings).where(SystemSettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = SystemSettings(id=1)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


@router.get("", response_model=SystemSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Return the current system settings."""
    settings = await _get_or_create_settings(db)
    return _orm_to_response(settings)


@router.patch("", response_model=SystemSettingsResponse)
async def update_settings(
    payload: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    """Update system settings (admin only). Partial updates supported."""
    settings = await _get_or_create_settings(db)

    if payload.branding:
        branding_data = payload.branding.model_dump(exclude_unset=True)
        if "logo_url" in branding_data:
            settings.logo_url = branding_data["logo_url"]
        if "primary_color" in branding_data:
            settings.primary_color = branding_data["primary_color"]
        if "company_name" in branding_data:
            settings.company_name = branding_data["company_name"]

    if payload.modules:
        modules_data = payload.modules.model_dump(exclude_unset=True)
        if "inventory" in modules_data:
            settings.module_inventory = modules_data["inventory"]
        if "vendors" in modules_data:
            settings.module_vendors = modules_data["vendors"]
        if "financials" in modules_data:
            settings.module_financials = modules_data["financials"]
        if "preventive_maintenance" in modules_data:
            settings.module_preventive_maintenance = modules_data["preventive_maintenance"]

    if payload.notifications:
        notif_data = payload.notifications.model_dump(exclude_unset=True)
        if "email_enabled" in notif_data:
            settings.notification_email_enabled = notif_data["email_enabled"]
        if "sms_enabled" in notif_data:
            settings.notification_sms_enabled = notif_data["sms_enabled"]
        if "slack_enabled" in notif_data:
            settings.notification_slack_enabled = notif_data["slack_enabled"]

    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return _orm_to_response(settings)
