import os
import sys
from datetime import datetime
from pymongo import MongoClient
import bcrypt


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ban_do_sv_sp")
ADMIN_SEED_USERNAME = os.getenv("ADMIN_SEED_USERNAME", "sysadmin")
ADMIN_SEED_PASSWORD = os.getenv("ADMIN_SEED_PASSWORD", "")


def seed_admin():
    if not ADMIN_SEED_PASSWORD or len(ADMIN_SEED_PASSWORD) < 8:
        print("ADMIN_SEED_PASSWORD phải có ít nhất 8 ký tự.", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to MongoDB at {MONGODB_URI}...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    admins_col = db["admins"]

    existing = admins_col.find_one({"username": ADMIN_SEED_USERNAME})
    if existing:
        print(f"Tài khoản '{ADMIN_SEED_USERNAME}' đã tồn tại, bỏ qua.")
        client.close()
        return

    password_hash = bcrypt.hashpw(
        ADMIN_SEED_PASSWORD.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    now = datetime.utcnow()
    admin_doc = {
        "username": ADMIN_SEED_USERNAME,
        "password_hash": password_hash,
        "display_name": "Quản trị hệ thống",
        "is_system_admin": True,
        "status": "active",
        "last_login_at": None,
        "created_at": now,
        "updated_at": now,
    }

    admins_col.insert_one(admin_doc)
    print(f"Đã tạo tài khoản quản trị hệ thống: '{ADMIN_SEED_USERNAME}'")
    client.close()


if __name__ == "__main__":
    try:
        seed_admin()
    except Exception as e:
        print(f"Lỗi seed admin: {e}", file=sys.stderr)
        sys.exit(1)
