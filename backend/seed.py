"""Seed script - creates the bootstrap admin and (optionally) demo clients.

Usage:
    python seed.py             # admin only
    python seed.py --demo      # admin + 25 demo clients for testing pagination
"""

import asyncio
import random
import sys

from app.core.config import settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.models.user import UserType
from app.services import user_service

CITIES = ["Tripoli", "Beirut", "Saida", "Zahle", "Tyre", "Byblos"]
FIRST = ["John", "Jane", "Ali", "Sara", "Omar", "Layla", "Karim", "Nour", "Hadi", "Rima"]
LAST = ["Doe", "Smith", "Hajjo", "Khoury", "Saad", "Haddad", "Nassar", "Fares"]


async def seed_admin() -> None:
    existing = await user_service.get_by_email(settings.FIRST_ADMIN_EMAIL)
    if existing:
        print(f"[=] Admin {settings.FIRST_ADMIN_EMAIL} already exists.")
        return
    await user_service.create_user(
        {
            "first_name": "Root",
            "last_name": "Admin",
            "email": settings.FIRST_ADMIN_EMAIL,
            "phone": "+96170000000",
            "city": "Tripoli",
            "age": 30,
            "password": settings.FIRST_ADMIN_PASSWORD,
        },
        user_type=UserType.ADMIN,
    )
    print(f"[+] Admin created: {settings.FIRST_ADMIN_EMAIL} / {settings.FIRST_ADMIN_PASSWORD}")


async def seed_demo_clients(count: int = 25) -> None:
    created = 0
    for i in range(count):
        email = f"user{i + 1}@example.com"
        if await user_service.get_by_email(email):
            continue
        await user_service.create_user(
            {
                "first_name": random.choice(FIRST),
                "last_name": random.choice(LAST),
                "email": email,
                "phone": f"+9617{random.randint(1000000, 9999999)}",
                "city": random.choice(CITIES),
                "age": random.randint(18, 60),
                "password": "Password123",
            },
            user_type=UserType.CLIENT,
        )
        created += 1
    print(f"[+] {created} demo clients created (password: Password123)")


async def main() -> None:
    await connect_to_mongo()
    try:
        await seed_admin()
        if "--demo" in sys.argv:
            await seed_demo_clients()
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
