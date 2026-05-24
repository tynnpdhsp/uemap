import uuid
from datetime import datetime, timedelta

from bson import ObjectId

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token


async def create_session(student_id: ObjectId, ip_address: str, user_agent: str) -> str:
    db = get_db()
    jti = str(uuid.uuid4())
    now = datetime.utcnow()

    expires_at = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    session_doc = {
        "student_id": student_id,
        "jti": jti,
        "expires_at": expires_at,
        "revoked_at": None,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "created_at": now,
    }

    await db["student_sessions"].insert_one(session_doc)

    token = create_access_token({"sub": str(student_id), "jti": jti}, role="student")
    return token


async def verify_session(jti: str) -> bool:
    db = get_db()
    now = datetime.utcnow()

    session = await db["student_sessions"].find_one({"jti": jti})
    if not session:
        return False

    if session.get("revoked_at") is not None:
        return False

    if session.get("expires_at") < now:
        return False

    return True


async def revoke_session(jti: str) -> None:
    db = get_db()
    now = datetime.utcnow()
    await db["student_sessions"].update_one(
        {"jti": jti, "revoked_at": None}, {"$set": {"revoked_at": now}}
    )


async def revoke_all_sessions(student_id: ObjectId) -> None:
    db = get_db()
    now = datetime.utcnow()
    await db["student_sessions"].update_many(
        {"student_id": student_id, "revoked_at": None}, {"$set": {"revoked_at": now}}
    )


async def revoke_other_sessions(student_id: ObjectId, current_jti: str) -> None:
    db = get_db()
    now = datetime.utcnow()
    await db["student_sessions"].update_many(
        {"student_id": student_id, "jti": {"$ne": current_jti}, "revoked_at": None},
        {"$set": {"revoked_at": now}},
    )
