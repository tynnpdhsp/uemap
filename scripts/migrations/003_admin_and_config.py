import os
import sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ban_do_sv_sp")


def run_migration():
    print(f"Connecting to MongoDB at {MONGODB_URI}...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]

    print("Configuring collection 'admins'...")
    admins_col = db["admins"]
    username_idx = admins_col.create_index([("username", ASCENDING)], unique=True)
    print(f"Created index on admins: {username_idx}")
    status_idx = admins_col.create_index([("status", ASCENDING)])
    print(f"Created index on admins: {status_idx}")

    print("Configuring collection 'admin_sessions'...")
    admin_sessions_col = db["admin_sessions"]
    jti_idx = admin_sessions_col.create_index([("jti", ASCENDING)], unique=True)
    print(f"Created index on admin_sessions: {jti_idx}")
    admin_session_compound_idx = admin_sessions_col.create_index([
        ("admin_id", ASCENDING),
        ("revoked_at", ASCENDING),
    ])
    print(f"Created index on admin_sessions: {admin_session_compound_idx}")

    print("Configuring collection 'admin_login_attempts'...")
    admin_login_attempts_col = db["admin_login_attempts"]
    ttl_idx = admin_login_attempts_col.create_index(
        [("failed_at", ASCENDING)],
        expireAfterSeconds=900,
    )
    print(f"Created TTL index on admin_login_attempts: {ttl_idx}")

    print("Adding 'admin_delete_reason' field support to 'comments'...")
    db["comments"].update_many(
        {"admin_delete_reason": {"$exists": False}},
        {"$set": {"admin_delete_reason": None}},
    )
    print("Updated comments collection.")

    print("Adding index {actor_id:1, occurred_at:-1} to 'audit_logs'...")
    audit_logs_col = db["audit_logs"]
    actor_idx = audit_logs_col.create_index([
        ("actor_id", ASCENDING),
        ("occurred_at", DESCENDING),
    ])
    print(f"Created index on audit_logs: {actor_idx}")

    print("Seeding email_templates in 'app_config'...")
    db["app_config"].update_one(
        {"_id": "email_templates"},
        {"$setOnInsert": {
            "activation": {
                "subject": "mã kích hoạt tài khoản bản đồ sinh viên sư phạm",
                "html_body": "<p>Xin chào {full_name}, mã OTP: {otp_code}</p>",
                "text_body": "Xin chào {full_name}, mã OTP: {otp_code}",
            },
            "password_reset": {
                "subject": "mã đặt lại mật khẩu bản đồ sinh viên sư phạm",
                "html_body": "<p>Xin chào {full_name}, mã đặt lại mật khẩu: {otp_code}</p>",
                "text_body": "Xin chào {full_name}, mã đặt lại mật khẩu: {otp_code}",
            },
            "updated_at": datetime.utcnow(),
        }},
        upsert=True,
    )
    print("Email templates config seeded.")

    print("Migration 003_admin_and_config.py completed successfully!")
    client.close()


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Error running migration: {e}", file=sys.stderr)
        sys.exit(1)
