import os
import sys
from pymongo import MongoClient, ASCENDING, DESCENDING


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ban_do_sv_sp")


def run_migration():
    print(f"Connecting to MongoDB at {MONGODB_URI}...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]

    print("Configuring collection 'students'...")
    students_col = db["students"]
    
    email_idx_name = students_col.create_index([("email", ASCENDING)], unique=True)
    print(f"Created index on students: {email_idx_name}")
    
    status_idx_name = students_col.create_index([("status", ASCENDING)])
    print(f"Created index on students: {status_idx_name}")

    print("Configuring collection 'otp_tokens'...")
    otp_tokens_col = db["otp_tokens"]
    otp_idx_name = otp_tokens_col.create_index([
        ("email", ASCENDING),
        ("purpose", ASCENDING),
        ("used_at", ASCENDING),
        ("expires_at", DESCENDING)
    ])
    print(f"Created index on otp_tokens: {otp_idx_name}")

    print("Configuring collection 'student_sessions'...")
    sessions_col = db["student_sessions"]
    
    jti_idx_name = sessions_col.create_index([("jti", ASCENDING)], unique=True)
    print(f"Created index on student_sessions: {jti_idx_name}")
    
    session_status_idx_name = sessions_col.create_index([
        ("student_id", ASCENDING),
        ("revoked_at", ASCENDING)
    ])
    print(f"Created index on student_sessions: {session_status_idx_name}")

    print("Configuring collection 'login_attempts'...")
    login_attempts_col = db["login_attempts"]
    
    ttl_idx_name = login_attempts_col.create_index(
        [("failed_at", ASCENDING)],
        expireAfterSeconds=900
    )
    print(f"Created TTL index on login_attempts: {ttl_idx_name}")

    print("Configuring collection 'audit_logs'...")
    audit_logs_col = db["audit_logs"]
    
    time_idx_name = audit_logs_col.create_index([("occurred_at", DESCENDING)])
    print(f"Created index on audit_logs: {time_idx_name}")
    
    event_time_idx_name = audit_logs_col.create_index([
        ("event_code", ASCENDING),
        ("occurred_at", DESCENDING)
    ])
    print(f"Created index on audit_logs: {event_time_idx_name}")

    print("Migration 001_students_and_auth.py completed successfully!")
    client.close()


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Error running migration: {e}", file=sys.stderr)
        sys.exit(1)
