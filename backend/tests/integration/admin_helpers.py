from datetime import datetime

from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app

ADMIN_USERNAME = "testadmin"
ADMIN_PASSWORD = "adminpass123"
ADMIN_DISPLAY = "Test Admin"


async def clean_admin_db() -> None:
    db = get_db()
    await db["admins"].delete_many({"username": {"$regex": "^test"}})
    await db["admin_sessions"].delete_many({})
    await db["admin_login_attempts"].delete_many({})
    await db["categories"].delete_many({"name": {"$regex": "^IntTest"}})
    await db["places"].delete_many({"name": {"$regex": "^IntTest"}})
    await db["reports"].delete_many({"report_code": {"$regex": "^INTEST"}})
    await db["comments"].delete_many({"content": {"$regex": "^IntTest"}})
    await db["students"].delete_many({"email": {"$regex": "^inttest"}})
    await db["audit_logs"].delete_many({})


async def seed_system_admin() -> ObjectId:
    db = get_db()
    now = datetime.utcnow()
    result = await db["admins"].insert_one({
        "username": ADMIN_USERNAME,
        "password_hash": hash_password(ADMIN_PASSWORD),
        "display_name": ADMIN_DISPLAY,
        "is_system_admin": True,
        "status": "active",
        "last_login_at": None,
        "created_at": now,
        "updated_at": now,
    })
    return result.inserted_id


async def admin_login(client: AsyncClient) -> str:
    res = await client.post("/api/admin/auth/login", json={
        "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD,
    })
    assert res.status_code == 200, res.text
    return res.json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def seed_student(email: str = "inttest_sv@student.hcmue.edu.vn", status: str = "active") -> ObjectId:
    db = get_db()
    now = datetime.utcnow()
    result = await db["students"].insert_one({
        "email": email,
        "password_hash": hash_password("password123"),
        "full_name": "IntTest SV",
        "status": status,
        "locked_reason": None,
        "activated_at": now if status == "active" else None,
        "created_at": now,
        "updated_at": now,
    })
    return result.inserted_id
