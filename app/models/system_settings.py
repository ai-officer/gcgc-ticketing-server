"""SystemSettings ORM model — single-row application configuration table."""
from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    # Enforced as a singleton at the application level (id always = 1)
    id = Column(Integer, primary_key=True, default=1)

    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(50), nullable=True, default="#1a56db")
    company_name = Column(String(255), nullable=True, default="GCG Ticketing System")

    # Module toggles
    module_inventory = Column(Boolean, default=True, nullable=False)
    module_vendors = Column(Boolean, default=True, nullable=False)
    module_financials = Column(Boolean, default=True, nullable=False)
    module_preventive_maintenance = Column(Boolean, default=True, nullable=False)

    # Notification toggles
    notification_email_enabled = Column(Boolean, default=False, nullable=False)
    notification_sms_enabled = Column(Boolean, default=False, nullable=False)
    notification_slack_enabled = Column(Boolean, default=False, nullable=False)
