from datetime import datetime

from bson import ObjectId

from app.core.database import get_db
from app.core.security import hash_password
from tests.e2e.helpers import api_client

ADMIN_USER = "e2e_sysadmin"
ADMIN_PASS = "e2eadminpass123"
ADMIN_DISPLAY = "E2E System Admin"

REGULAR_ADMIN_USER = "e2e_regular"
REGULAR_ADMIN_PASS = "e2eregularpass123"

STUDENT_EMAIL = "4901104188@student.hcmue.edu.vn"
STUDENT_PASS = "studentpass123"
STUDENT_NAME = "E2E Student"


async def clean_admin_e2e_db():
    db = get_db()
    await db["admins"].delete_many({"username": {"$regex": "^e2e_"}})
    await db["admin_sessions"].delete_many({})
    await db["admin_login_attempts"].delete_many({})
    await db["categories"].delete_many({"name": {"$regex": "^E2E_"}})
    await db["places"].delete_many({"name": {"$regex": "^E2E_"}})
    await db["comments"].delete_many({"content": {"$regex": "^E2E_"}})
    await db["reports"].delete_many({"report_code": {"$regex": "^E2E"}})
    await db["students"].delete_many({"email": STUDENT_EMAIL})
    await db["audit_logs"].delete_many({})
    await db["student_sessions"].delete_many({})
    await db["app_config"].delete_many({"_id": {"$in": ["map", "email_templates"]}})


async def seed_system_admin() -> ObjectId:
    db = get_db()
    now = datetime.utcnow()
    result = await db["admins"].insert_one({
        "username": ADMIN_USER,
        "password_hash": hash_password(ADMIN_PASS),
        "display_name": ADMIN_DISPLAY,
        "is_system_admin": True,
        "status": "active",
        "last_login_at": None,
        "created_at": now,
        "updated_at": now,
    })
    return result.inserted_id


async def admin_login_token(client, username=ADMIN_USER, password=ADMIN_PASS) -> str:
    res = await client.post("/api/admin/auth/login", json={
        "username": username, "password": password,
    })
    assert res.status_code == 200, res.text
    return res.json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def seed_active_student() -> ObjectId:
    db = get_db()
    now = datetime.utcnow()
    result = await db["students"].insert_one({
        "email": STUDENT_EMAIL,
        "password_hash": hash_password(STUDENT_PASS),
        "full_name": STUDENT_NAME,
        "status": "active",
        "locked_reason": None,
        "activated_at": now,
        "created_at": now,
        "updated_at": now,
    })
    return result.inserted_id


async def seed_category(name: str = "E2E_Ăn uống") -> ObjectId:
    db = get_db()
    now = datetime.utcnow()
    result = await db["categories"].insert_one({
        "name": name,
        "color": "#FF6600",
        "order": 0,
        "is_hidden": False,
        "created_at": now,
        "updated_at": now,
    })
    return result.inserted_id


async def seed_place(cat_id: ObjectId, student_id: ObjectId, name: str = "E2E_Quán cà phê") -> int:
    db = get_db()
    now = datetime.utcnow()
    last = await db["places"].find_one({}, sort=[("public_id", -1)])
    public_id = (last["public_id"] + 1) if last and "public_id" in last else 1
    await db["places"].insert_one({
        "public_id": public_id,
        "creator_student_id": student_id,
        "category_id": cat_id,
        "name": name,
        "description": "Mô tả E2E",
        "address": "123 Đường Test",
        "scope_type": "public",
        "location": {"type": "Point", "coordinates": [106.68, 10.76]},
        "hours": None,
        "contact": None,
        "status": "published",
        "hidden_note": None,
        "images": [],
        "video": None,
        "published_at": now,
        "deleted_at": None,
        "created_at": now,
        "updated_at": now,
    })
    return public_id
