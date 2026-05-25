from datetime import datetime

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.database import get_db
from app.core.security import hash_password
from app.services import audit_service
from app.services.admin_auth_service import ADMIN_STATUS_LABELS


async def list_admins() -> list:
    db = get_db()
    admins = await db["admins"].find().sort("created_at", -1).to_list(None)
    return [_format_admin(a) for a in admins]


async def create_admin(
    username: str, password: str, display_name: str, admin_id: ObjectId, ip_address: str
) -> dict:
    db = get_db()

    existing = await db["admins"].find_one({"username": username})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_USERNAME_EXISTS",
                    "message": "Tên đăng nhập đã tồn tại.",
                    "details": [],
                },
            },
        )

    now = datetime.utcnow()
    doc = {
        "username": username,
        "password_hash": hash_password(password),
        "display_name": display_name,
        "is_system_admin": False,
        "status": "active",
        "last_login_at": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await db["admins"].insert_one(doc)

    await audit_service.log_event(
        event_code="ADMIN_ACCOUNT_CREATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="admin",
        object_id=str(result.inserted_id),
        result="success",
        description=f"Tạo tài khoản quản trị '{username}' thành công.",
        ip_address=ip_address,
    )

    doc["_id"] = result.inserted_id
    return _format_admin(doc)


async def update_admin(target_id: str, data: dict, admin_id: ObjectId, ip_address: str) -> dict:
    db = get_db()
    try:
        target_oid = ObjectId(target_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_NOT_FOUND",
                    "message": "Không tìm thấy tài khoản quản trị.",
                    "details": [],
                },
            },
        )

    admin_doc = await db["admins"].find_one({"_id": target_oid})
    if not admin_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_NOT_FOUND",
                    "message": "Không tìm thấy tài khoản quản trị.",
                    "details": [],
                },
            },
        )

    update_fields: dict = {"updated_at": datetime.utcnow()}
    if data.get("display_name"):
        update_fields["display_name"] = data["display_name"]
    if data.get("password"):
        update_fields["password_hash"] = hash_password(data["password"])

    await db["admins"].update_one({"_id": target_oid}, {"$set": update_fields})

    await audit_service.log_event(
        event_code="ADMIN_ACCOUNT_UPDATE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="admin",
        object_id=target_id,
        result="success",
        description=f"Cập nhật tài khoản quản trị '{admin_doc['username']}'.",
        ip_address=ip_address,
    )

    updated = await db["admins"].find_one({"_id": target_oid})
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_NOT_FOUND",
                    "message": "Không tìm thấy tài khoản quản trị.",
                    "details": [],
                },
            },
        )
    return _format_admin(updated)


async def disable_admin(target_id: str, admin_id: ObjectId, ip_address: str) -> None:
    db = get_db()
    try:
        target_oid = ObjectId(target_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_NOT_FOUND",
                    "message": "Không tìm thấy tài khoản quản trị.",
                    "details": [],
                },
            },
        )

    if target_oid == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_CANNOT_DISABLE_SELF",
                    "message": "Không thể tự vô hiệu hóa chính mình.",
                    "details": [],
                },
            },
        )

    admin_doc = await db["admins"].find_one({"_id": target_oid})
    if not admin_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "ADMIN_NOT_FOUND",
                    "message": "Không tìm thấy tài khoản quản trị.",
                    "details": [],
                },
            },
        )

    if admin_doc.get("is_system_admin"):
        active_sys_count = await db["admins"].count_documents(
            {"is_system_admin": True, "status": "active"}
        )
        if active_sys_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "ADMIN_CANNOT_DISABLE_SELF",
                        "message": "Không thể vô hiệu hóa tài khoản quản trị hệ thống duy nhất còn hoạt động.",
                        "details": [],
                    },
                },
            )

    now = datetime.utcnow()
    await db["admins"].update_one(
        {"_id": target_oid},
        {"$set": {"status": "disabled", "updated_at": now}},
    )

    await db["admin_sessions"].update_many(
        {"admin_id": target_oid, "revoked_at": None},
        {"$set": {"revoked_at": now}},
    )

    await audit_service.log_event(
        event_code="ADMIN_ACCOUNT_DISABLE",
        actor_role="admin",
        actor_id=admin_id,
        object_type="admin",
        object_id=target_id,
        result="success",
        description=f"Vô hiệu hóa tài khoản quản trị '{admin_doc['username']}'.",
        ip_address=ip_address,
    )


def _format_admin(admin: dict) -> dict:
    return {
        "id": str(admin["_id"]),
        "username": admin["username"],
        "display_name": admin["display_name"],
        "is_system_admin": admin.get("is_system_admin", False),
        "status": admin["status"],
        "status_label": ADMIN_STATUS_LABELS.get(admin["status"], admin["status"]),
        "last_login_at": admin.get("last_login_at"),
        "created_at": admin["created_at"],
    }
