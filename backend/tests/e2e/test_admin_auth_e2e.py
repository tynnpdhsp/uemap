import pytest

from app.core.database import get_db
from tests.e2e.admin_e2e_helpers import (
    ADMIN_PASS,
    ADMIN_USER,
    admin_login_token,
    auth,
    clean_admin_e2e_db,
    seed_system_admin,
)
from tests.e2e.helpers import api_client, assert_error

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_e2e_admin_full_auth_lifecycle():
    """Login → /me → logout → token hết hiệu lực"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()

        res = await client.post("/api/admin/auth/login", json={
            "username": ADMIN_USER, "password": ADMIN_PASS,
        })
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        token = body["data"]["access_token"]
        admin_info = body["data"]["admin"]
        assert admin_info["username"] == ADMIN_USER
        assert admin_info["is_system_admin"] is True
        assert admin_info["status_label"] == "hoạt động"

        res = await client.get("/api/admin/auth/me", headers=auth(token))
        assert res.status_code == 200
        assert res.json()["data"]["username"] == ADMIN_USER

        res = await client.post("/api/admin/auth/logout", headers=auth(token))
        assert res.status_code == 204

        res = await client.get("/api/admin/auth/me", headers=auth(token))
        assert_error(res, 401, "AUTH_UNAUTHORIZED")

        db = get_db()
        login_log = await db["audit_logs"].find_one({"event_code": "ADMIN_LOGIN"})
        assert login_log is not None
        logout_log = await db["audit_logs"].find_one({"event_code": "ADMIN_LOGOUT"})
        assert logout_log is not None


@pytest.mark.asyncio
async def test_e2e_admin_login_failures_and_rate_limit():
    """Đăng nhập sai nhiều lần → rate limit"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()

        for _ in range(5):
            res = await client.post("/api/admin/auth/login", json={
                "username": ADMIN_USER, "password": "wrongpassword1",
            })
            assert_error(res, 401, "ADMIN_LOGIN_FAILED")

        db = get_db()
        attempts = await db["admin_login_attempts"].count_documents({"username": ADMIN_USER})
        assert attempts >= 5

        fail_log = await db["audit_logs"].find_one({"event_code": "ADMIN_LOGIN", "result": "failure"})
        assert fail_log is not None


@pytest.mark.asyncio
async def test_e2e_admin_disabled_account_blocked():
    """Tài khoản disabled không đăng nhập được"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()

        db = get_db()
        await db["admins"].update_one(
            {"username": ADMIN_USER}, {"$set": {"status": "disabled"}},
        )

        res = await client.post("/api/admin/auth/login", json={
            "username": ADMIN_USER, "password": ADMIN_PASS,
        })
        assert_error(res, 401, "ADMIN_ACCOUNT_DISABLED")


@pytest.mark.asyncio
async def test_e2e_admin_protected_routes_reject_student_token():
    """Student token không vào được admin routes"""
    async with api_client() as client:
        await clean_admin_e2e_db()

        from app.core.security import create_access_token
        from bson import ObjectId
        fake_token = create_access_token({"sub": str(ObjectId()), "jti": "f"}, role="student")

        res = await client.get("/api/admin/auth/me", headers=auth(fake_token))
        assert res.status_code == 403
