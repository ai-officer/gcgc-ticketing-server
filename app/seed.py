"""Seed script — populates the database with initial mock data.

Run from the backend/ directory:
    python -m app.seed

The script is idempotent: it will skip rows that already exist
(checked via email for users, name for most lookup tables, id for
explicit-id rows).
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.database import AsyncSessionLocal, engine, Base

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_PASSWORD = "gcgc2024"
NOW = datetime.now(timezone.utc)


async def create_tables() -> None:
    """Ensure all tables exist (create if not present)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables verified / created.")


async def seed_users(db: AsyncSession) -> dict[str, int]:
    """Insert users and return a mapping of legacy-id → real DB id."""
    from app.models.user import User
    from sqlalchemy import select

    users_data = [
        {"legacy": "u1", "name": "Admin User", "email": "admin@gcgc.com", "role": "admin", "is_on_duty": True},
        {"legacy": "u2", "name": "Tech John", "email": "john@gcgc.com", "role": "technician", "is_on_duty": True},
        {"legacy": "u3", "name": "Tech Sarah", "email": "sarah@gcgc.com", "role": "technician", "is_on_duty": False},
        {"legacy": "u4", "name": "Req Alice", "email": "alice@hotel.com", "role": "requestor", "is_on_duty": True},
        {"legacy": "u5", "name": "Desk Bob", "email": "bob@gcgc.com", "role": "service_desk", "is_on_duty": True},
    ]

    id_map: dict[str, int] = {}
    hashed = hash_password(DEFAULT_PASSWORD)

    for u in users_data:
        result = await db.execute(select(User).where(User.email == u["email"]))
        existing = result.scalar_one_or_none()
        if existing:
            id_map[u["legacy"]] = existing.id
            logger.info("  User %s already exists (id=%d)", u["email"], existing.id)
        else:
            user = User(
                name=u["name"],
                email=u["email"],
                hashed_password=hashed,
                role=u["role"],
                is_on_duty=u["is_on_duty"],
            )
            db.add(user)
            await db.flush()
            id_map[u["legacy"]] = user.id
            logger.info("  Created user %s (id=%d)", u["email"], user.id)

    await db.commit()
    return id_map


async def seed_properties(db: AsyncSession) -> dict[str, int]:
    from app.models.property import Property
    from sqlalchemy import select

    props_data = [
        {"legacy": "p1", "name": "Hotel Sogo", "description": "Budget hotel chain", "collection_target": 500000},
        {"legacy": "p2", "name": "Eurotel", "description": "European-themed hotel", "collection_target": 300000},
    ]

    id_map: dict[str, int] = {}
    for p in props_data:
        result = await db.execute(select(Property).where(Property.name == p["name"]))
        existing = result.scalar_one_or_none()
        if existing:
            id_map[p["legacy"]] = existing.id
        else:
            prop = Property(
                name=p["name"],
                description=p["description"],
                collection_target=p["collection_target"],
            )
            db.add(prop)
            await db.flush()
            id_map[p["legacy"]] = prop.id
            logger.info("  Created property %s (id=%d)", p["name"], prop.id)

    await db.commit()
    return id_map


async def seed_locations(db: AsyncSession, prop_map: dict[str, int]) -> dict[str, int]:
    from app.models.location import Location
    from sqlalchemy import select

    locs_data = [
        {"legacy": "l1", "property": "p1", "name": "Cubao", "address": "Aurora Blvd, Cubao"},
        {"legacy": "l2", "property": "p1", "name": "Makati", "address": "Makati Ave"},
        {"legacy": "l3", "property": "p2", "name": "North EDSA", "address": "EDSA, Quezon City"},
        {"legacy": "l4", "property": "p2", "name": "Pedro Gil", "address": "Pedro Gil St, Manila"},
    ]

    id_map: dict[str, int] = {}
    for l in locs_data:
        pid = prop_map[l["property"]]
        result = await db.execute(
            select(Location).where(Location.name == l["name"], Location.property_id == pid)
        )
        existing = result.scalar_one_or_none()
        if existing:
            id_map[l["legacy"]] = existing.id
        else:
            loc = Location(property_id=pid, name=l["name"], address=l["address"])
            db.add(loc)
            await db.flush()
            id_map[l["legacy"]] = loc.id
            logger.info("  Created location %s (id=%d)", l["name"], loc.id)

    await db.commit()
    return id_map


async def seed_assets(
    db: AsyncSession, prop_map: dict[str, int], loc_map: dict[str, int]
) -> dict[str, int]:
    from app.models.asset import Asset
    from sqlalchemy import select
    from datetime import date

    assets_data = [
        {
            "legacy": "a1", "name": "HVAC Unit - Lobby", "category": "HVAC",
            "property": "p1", "location": "l1", "status": "active",
            "manufacturer": "Carrier", "model": "X-2000", "serial_number": "SN-HVAC-001",
            "purchase_date": date(2023, 1, 15), "warranty_expiry": date(2028, 1, 15),
            "last_maintenance": date(2024, 2, 10), "next_maintenance": date(2024, 8, 10),
        },
        {
            "legacy": "a2", "name": "Industrial Oven", "category": "Kitchen Equipment",
            "property": "p1", "location": "l1", "status": "maintenance",
            "manufacturer": "Vulcan", "model": "V-500", "serial_number": "SN-OVEN-002",
            "purchase_date": date(2022, 5, 20), "warranty_expiry": date(2025, 5, 20),
            "last_maintenance": date(2024, 1, 5), "next_maintenance": date(2024, 7, 5),
        },
        {
            "legacy": "a3", "name": "Elevator 1", "category": "Elevator",
            "property": "p2", "location": "l3", "status": "active",
            "manufacturer": "Otis", "model": "Gen2", "serial_number": "SN-ELEV-003",
            "purchase_date": date(2020, 11, 10), "warranty_expiry": date(2030, 11, 10),
            "last_maintenance": date(2024, 3, 1), "next_maintenance": date(2024, 6, 1),
        },
    ]

    id_map: dict[str, int] = {}
    for a in assets_data:
        result = await db.execute(select(Asset).where(Asset.serial_number == a["serial_number"]))
        existing = result.scalar_one_or_none()
        if existing:
            id_map[a["legacy"]] = existing.id
        else:
            asset = Asset(
                name=a["name"], category=a["category"],
                property_id=prop_map[a["property"]], location_id=loc_map[a["location"]],
                status=a["status"], manufacturer=a["manufacturer"], model=a["model"],
                serial_number=a["serial_number"], purchase_date=a["purchase_date"],
                warranty_expiry=a["warranty_expiry"], last_maintenance=a["last_maintenance"],
                next_maintenance=a["next_maintenance"],
            )
            db.add(asset)
            await db.flush()
            id_map[a["legacy"]] = asset.id
            logger.info("  Created asset %s (id=%d)", a["name"], asset.id)

    await db.commit()
    return id_map


async def seed_vendors(db: AsyncSession) -> dict[str, int]:
    from app.models.vendor import Vendor
    from sqlalchemy import select

    vendors_data = [
        {"legacy": "v1", "name": "Otis Elevators", "contact_name": "John Smith",
         "email": "john@otis.com", "phone": "555-0101", "specialty": "Elevators",
         "contract_status": "active", "sla_hours": 4},
        {"legacy": "v2", "name": "CoolBreeze HVAC", "contact_name": "Sarah Connor",
         "email": "sarah@coolbreeze.com", "phone": "555-0102", "specialty": "HVAC",
         "contract_status": "active", "sla_hours": 12},
        {"legacy": "v3", "name": "QuickFix Plumbing", "contact_name": "Mario Bros",
         "email": "mario@quickfix.com", "phone": "555-0103", "specialty": "Plumbing",
         "contract_status": "pending", "sla_hours": 24},
    ]

    id_map: dict[str, int] = {}
    for v in vendors_data:
        result = await db.execute(select(Vendor).where(Vendor.email == v["email"]))
        existing = result.scalar_one_or_none()
        if existing:
            id_map[v["legacy"]] = existing.id
        else:
            vendor = Vendor(**{k: val for k, val in v.items() if k != "legacy"})
            db.add(vendor)
            await db.flush()
            id_map[v["legacy"]] = vendor.id
            logger.info("  Created vendor %s (id=%d)", v["name"], vendor.id)

    await db.commit()
    return id_map


async def seed_inventory(
    db: AsyncSession, prop_map: dict[str, int], loc_map: dict[str, int]
) -> dict[str, int]:
    from app.models.inventory_item import InventoryItem
    from sqlalchemy import select

    items_data = [
        {"legacy": "i1", "name": "LED Bulb 60W", "sku": "SKU-LED-001", "category": "Electrical",
         "quantity": 50, "min_quantity": 10, "unit_cost": 5.99, "property": "p1", "location": "l1"},
        {"legacy": "i2", "name": "AC Filter 16x20", "sku": "SKU-ACF-002", "category": "HVAC",
         "quantity": 8, "min_quantity": 5, "unit_cost": 12.50, "property": "p1", "location": "l2"},
        {"legacy": "i3", "name": "Faucet Cartridge", "sku": "SKU-FC-003", "category": "Plumbing",
         "quantity": 3, "min_quantity": 5, "unit_cost": 22.00, "property": "p2", "location": "l3"},
    ]

    id_map: dict[str, int] = {}
    for item in items_data:
        result = await db.execute(select(InventoryItem).where(InventoryItem.sku == item["sku"]))
        existing = result.scalar_one_or_none()
        if existing:
            id_map[item["legacy"]] = existing.id
        else:
            inv = InventoryItem(
                name=item["name"], sku=item["sku"], category=item["category"],
                quantity=item["quantity"], min_quantity=item["min_quantity"],
                unit_cost=item["unit_cost"],
                property_id=prop_map[item["property"]],
                location_id=loc_map[item["location"]],
            )
            db.add(inv)
            await db.flush()
            id_map[item["legacy"]] = inv.id
            logger.info("  Created inventory item %s (id=%d)", item["name"], inv.id)

    await db.commit()
    return id_map


async def seed_service_categories(db: AsyncSession) -> None:
    from app.models.service_category import ServiceCategory
    from sqlalchemy import select

    cats_data = [
        {"name": "Plumbing", "description": "Water and drainage issues"},
        {"name": "Electrical", "description": "Power and lighting issues"},
        {"name": "HVAC", "description": "Heating, ventilation, and air conditioning"},
        {"name": "General Maintenance", "description": "Miscellaneous maintenance tasks"},
    ]

    for c in cats_data:
        result = await db.execute(select(ServiceCategory).where(ServiceCategory.name == c["name"]))
        if not result.scalar_one_or_none():
            db.add(ServiceCategory(**c))
            logger.info("  Created category %s", c["name"])

    await db.commit()


async def seed_incident_types(db: AsyncSession) -> None:
    from app.models.incident_type import IncidentType
    from sqlalchemy import select

    its_data = [
        {"name": "Critical", "sla_hours": 4, "response_sla_hours": 1, "resolution_sla_hours": 4,
         "description": "Critical system failure"},
        {"name": "High", "sla_hours": 8, "response_sla_hours": 2, "resolution_sla_hours": 8,
         "description": "High priority issue"},
        {"name": "Medium", "sla_hours": 24, "response_sla_hours": 4, "resolution_sla_hours": 24,
         "description": "Medium priority issue"},
        {"name": "Low", "sla_hours": 72, "response_sla_hours": 8, "resolution_sla_hours": 72,
         "description": "Low priority issue"},
    ]

    for it in its_data:
        result = await db.execute(select(IncidentType).where(IncidentType.name == it["name"]))
        if not result.scalar_one_or_none():
            db.add(IncidentType(**it))
            logger.info("  Created incident type %s", it["name"])

    await db.commit()


async def seed_request_templates(db: AsyncSession) -> None:
    from app.models.request_template import RequestTemplate
    from sqlalchemy import select

    templates_data = [
        {"name": "Leaking Pipe", "category": "Plumbing", "priority": "high",
         "description": "Report a leaking pipe issue"},
        {"name": "Power Outage", "category": "Electrical", "priority": "critical",
         "description": "Report a power outage"},
        {"name": "AC Not Cooling", "category": "HVAC", "priority": "medium",
         "description": "Air conditioning not cooling properly"},
        {"name": "Network Down", "category": "IT", "priority": "high",
         "description": "Network connectivity issue"},
    ]

    for t in templates_data:
        result = await db.execute(select(RequestTemplate).where(RequestTemplate.name == t["name"]))
        if not result.scalar_one_or_none():
            db.add(RequestTemplate(**t))
            logger.info("  Created template %s", t["name"])

    await db.commit()


async def seed_pm_schedules(
    db: AsyncSession,
    prop_map: dict[str, int],
    asset_map: dict[str, int],
    user_map: dict[str, int],
) -> dict[str, int]:
    from app.models.preventive_maintenance import PreventiveMaintenance
    from sqlalchemy import select

    # Compute next_due_dates relative to now per requirements
    pms_data = [
        {
            "legacy": "pm1",
            "title": "Monthly AC Cleaning",
            "description": "Clean and inspect all AC units",
            "property": "p1",
            "asset": "a1",
            "frequency": "monthly",
            "status": "active",
            "assigned_to": "u2",
            "next_due_date": NOW + timedelta(days=7),
        },
        {
            "legacy": "pm2",
            "title": "Quarterly Elevator Inspection",
            "description": "Full inspection of elevator systems",
            "property": "p2",
            "asset": "a3",
            "frequency": "quarterly",
            "status": "active",
            "assigned_to": "u2",
            "next_due_date": NOW + timedelta(days=14),
        },
        {
            "legacy": "pm3",
            "title": "Bi-annual Fire Safety Check",
            "description": "Inspect fire extinguishers and alarms",
            "property": "p1",
            "asset": None,
            "frequency": "biannually",
            "status": "active",
            "assigned_to": None,
            "next_due_date": NOW + timedelta(days=30),
        },
    ]

    id_map: dict[str, int] = {}
    for pm in pms_data:
        result = await db.execute(
            select(PreventiveMaintenance).where(PreventiveMaintenance.title == pm["title"])
        )
        existing = result.scalar_one_or_none()
        if existing:
            id_map[pm["legacy"]] = existing.id
        else:
            record = PreventiveMaintenance(
                title=pm["title"],
                description=pm["description"],
                property_id=prop_map[pm["property"]],
                asset_id=asset_map[pm["asset"]] if pm["asset"] else None,
                frequency=pm["frequency"],
                status=pm["status"],
                assigned_to_id=user_map[pm["assigned_to"]] if pm["assigned_to"] else None,
                next_due_date=pm["next_due_date"],
            )
            db.add(record)
            await db.flush()
            id_map[pm["legacy"]] = record.id
            logger.info("  Created PM schedule %s (id=%d)", pm["title"], record.id)

    await db.commit()
    return id_map


async def seed_announcements(db: AsyncSession, user_map: dict[str, int]) -> None:
    from app.models.announcement import Announcement
    from sqlalchemy import select

    anns_data = [
        {"title": "System Maintenance Tonight",
         "content": "Scheduled maintenance from 2AM-4AM. Expect brief outages.",
         "author": "u1"},
        {"title": "New SLA Policy",
         "content": "Updated SLA policies are now in effect. Please review the updated response time targets.",
         "author": "u1"},
    ]

    for a in anns_data:
        result = await db.execute(select(Announcement).where(Announcement.title == a["title"]))
        if not result.scalar_one_or_none():
            ann = Announcement(
                title=a["title"],
                content=a["content"],
                author_id=user_map[a["author"]],
            )
            db.add(ann)
            logger.info("  Created announcement: %s", a["title"])

    await db.commit()


async def seed_tickets(
    db: AsyncSession,
    user_map: dict[str, int],
    prop_map: dict[str, int],
    loc_map: dict[str, int],
    asset_map: dict[str, int],
    vendor_map: dict[str, int],
) -> None:
    from app.models.ticket import Ticket, TicketTask, TicketRating
    from sqlalchemy import select

    # First, reset the tickets sequence to start at 1001
    await db.execute(
        text("SELECT setval('tickets_id_seq', 1000, true)")
    )

    tickets_data = [
        {
            "id": 1001,
            "title": "AC not working in Room 302",
            "description": "The air conditioning unit in room 302 stopped working.",
            "category": "HVAC",
            "priority": "high",
            "status": "in-progress",
            "requestor": "u4",
            "assignee": "u2",
            "vendor": None,
            "property": "p1",
            "location": "l1",
            "room_number": "302",
            "asset": "a1",
            "cost": 150,
            "vendor_cost": None,
            "tasks": [
                {"description": "Inspect AC unit", "is_completed": True},
                {"description": "Replace filter", "is_completed": False},
            ],
            "rating": None,
        },
        {
            "id": 1002,
            "title": "Leaking pipe in kitchen",
            "description": "Water leak under the kitchen sink.",
            "category": "Plumbing",
            "priority": "critical",
            "status": "open",
            "requestor": "u4",
            "assignee": None,
            "vendor": None,
            "property": "p1",
            "location": "l2",
            "room_number": None,
            "asset": None,
            "cost": 0,
            "vendor_cost": None,
            "tasks": [],
            "rating": None,
        },
        {
            "id": 1003,
            "title": "Elevator maintenance required",
            "description": "Elevator making unusual noise.",
            "category": "Elevator",
            "priority": "medium",
            "status": "resolved",
            "requestor": "u4",
            "assignee": "u3",
            "vendor": "v1",
            "property": "p2",
            "location": "l3",
            "room_number": None,
            "asset": "a3",
            "cost": 500,
            "vendor_cost": 450,
            "tasks": [],
            "rating": {"score": 4, "feedback": "Good job, fixed quickly"},
        },
        {
            "id": 1004,
            "title": "Lobby lights flickering",
            "description": "Lobby lighting flickering intermittently.",
            "category": "Electrical",
            "priority": "low",
            "status": "assigned",
            "requestor": "u4",
            "assignee": "u2",
            "vendor": None,
            "property": "p2",
            "location": "l4",
            "room_number": None,
            "asset": None,
            "cost": 80,
            "vendor_cost": None,
            "tasks": [],
            "rating": None,
        },
    ]

    for t in tickets_data:
        result = await db.execute(select(Ticket).where(Ticket.id == t["id"]))
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("  Ticket TKT-%04d already exists", t["id"])
            continue

        ticket = Ticket(
            id=t["id"],
            title=t["title"],
            description=t["description"],
            category=t["category"],
            priority=t["priority"],
            status=t["status"],
            requestor_id=user_map.get(t["requestor"]) if t["requestor"] else None,
            assignee_id=user_map.get(t["assignee"]) if t["assignee"] else None,
            vendor_id=vendor_map.get(t["vendor"]) if t["vendor"] else None,
            property_id=prop_map.get(t["property"]) if t["property"] else None,
            location_id=loc_map.get(t["location"]) if t["location"] else None,
            room_number=t["room_number"],
            asset_id=asset_map.get(t["asset"]) if t["asset"] else None,
            cost=t["cost"],
            vendor_cost=t["vendor_cost"],
            resolved_at=NOW if t["status"] == "resolved" else None,
        )
        db.add(ticket)
        await db.flush()

        for task_data in t.get("tasks", []):
            db.add(TicketTask(
                ticket_id=ticket.id,
                description=task_data["description"],
                is_completed=task_data["is_completed"],
            ))

        if t.get("rating"):
            db.add(TicketRating(
                ticket_id=ticket.id,
                score=t["rating"]["score"],
                feedback=t["rating"]["feedback"],
            ))

        logger.info("  Created ticket TKT-%04d: %s", ticket.id, ticket.title)

    await db.commit()

    # Advance the sequence so the next auto-generated ticket gets id > 1004
    await db.execute(text("SELECT setval('tickets_id_seq', 1004, true)"))
    await db.commit()
    logger.info("  Ticket sequence set to 1004")


async def seed_system_settings(db: AsyncSession) -> None:
    from app.models.system_settings import SystemSettings
    from sqlalchemy import select

    result = await db.execute(select(SystemSettings).where(SystemSettings.id == 1))
    if not result.scalar_one_or_none():
        db.add(SystemSettings(
            id=1,
            logo_url=None,
            primary_color="#1a56db",
            company_name="GCG Ticketing System",
            module_inventory=True,
            module_vendors=True,
            module_financials=True,
            module_preventive_maintenance=True,
            notification_email_enabled=False,
            notification_sms_enabled=False,
            notification_slack_enabled=False,
        ))
        await db.commit()
        logger.info("  Created default system settings")


async def run_seed() -> None:
    """Execute all seed operations in dependency order."""
    logger.info("=== Starting database seed ===")

    # 1. Ensure tables exist
    await create_tables()

    async with AsyncSessionLocal() as db:
        logger.info("Seeding users...")
        user_map = await seed_users(db)

        logger.info("Seeding properties...")
        prop_map = await seed_properties(db)

        logger.info("Seeding locations...")
        loc_map = await seed_locations(db, prop_map)

        logger.info("Seeding assets...")
        asset_map = await seed_assets(db, prop_map, loc_map)

        logger.info("Seeding vendors...")
        vendor_map = await seed_vendors(db)

        logger.info("Seeding inventory...")
        await seed_inventory(db, prop_map, loc_map)

        logger.info("Seeding service categories...")
        await seed_service_categories(db)

        logger.info("Seeding incident types...")
        await seed_incident_types(db)

        logger.info("Seeding request templates...")
        await seed_request_templates(db)

        logger.info("Seeding preventive maintenance schedules...")
        await seed_pm_schedules(db, prop_map, asset_map, user_map)

        logger.info("Seeding announcements...")
        await seed_announcements(db, user_map)

        logger.info("Seeding tickets...")
        await seed_tickets(db, user_map, prop_map, loc_map, asset_map, vendor_map)

        logger.info("Seeding system settings...")
        await seed_system_settings(db)

    logger.info("=== Seed completed successfully ===")


if __name__ == "__main__":
    asyncio.run(run_seed())
