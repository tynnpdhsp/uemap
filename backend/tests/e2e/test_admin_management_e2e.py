from datetime import datetime, timedelta

import pytest

from app.core.database import get_db
from tests.e2e.admin_e2e_helpers import (
    REGULAR_ADMIN_PASS,
    REGULAR_ADMIN_USER,
    admin_login_token,
    auth,
    clean_admin_e2e_db,
    seed_active_student,
    seed_category,
    seed_place,
    seed_system_admin,
)
from tests.e2e.helpers import api_client, assert_error

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_e2e_admin_manages_categories():
    """System admin: tạo → sửa → ẩn → bỏ ẩn → xóa danh mục"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        token = await admin_login_token(client)
        h = auth(token)

        res = await client.post(
            "/api/admin/categories",
            headers=h,
            json={
                "name": "E2E_Thể thao",
                "color": "#00FF00",
                "order": 1,
            },
        )
        assert res.status_code == 201
        cat_id = res.json()["data"]["id"]

        res = await client.patch(
            f"/api/admin/categories/{cat_id}",
            headers=h,
            json={
                "name": "E2E_Giải trí",
            },
        )
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "E2E_Giải trí"

        res = await client.patch(
            f"/api/admin/categories/{cat_id}/hide",
            headers=h,
            json={
                "is_hidden": True,
            },
        )
        assert res.status_code == 200
        assert res.json()["data"]["is_hidden"] is True

        res = await client.patch(
            f"/api/admin/categories/{cat_id}/hide",
            headers=h,
            json={
                "is_hidden": False,
            },
        )
        assert res.status_code == 200
        assert res.json()["data"]["is_hidden"] is False

        res = await client.delete(f"/api/admin/categories/{cat_id}", headers=h)
        assert res.status_code == 204

        db = get_db()
        codes = {d["event_code"] async for d in db["audit_logs"].find({})}
        assert "CATEGORY_CREATE" in codes
        assert "CATEGORY_UPDATE" in codes
        assert "CATEGORY_HIDE" in codes
        assert "CATEGORY_DELETE" in codes


@pytest.mark.asyncio
async def test_e2e_admin_lock_unlock_student():
    """Admin khóa SV → session bị revoke → mở khóa"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        token = await admin_login_token(client)
        h = auth(token)

        db = get_db()
        await db["student_sessions"].insert_one(
            {
                "student_id": sid,
                "jti": "e2e-sv-jti",
                "revoked_at": None,
                "expires_at": datetime.utcnow() + timedelta(days=7),
            }
        )

        res = await client.patch(
            f"/api/admin/students/{sid}/lock",
            headers=h,
            json={
                "locked_reason": "Vi phạm quy định sử dụng hệ thống",
            },
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "locked"

        session = await db["student_sessions"].find_one({"jti": "e2e-sv-jti"})
        assert session["revoked_at"] is not None

        res = await client.get(f"/api/admin/students/{sid}", headers=h)
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "locked"
        assert res.json()["data"]["status_label"] == "bị khóa"

        res = await client.patch(f"/api/admin/students/{sid}/unlock", headers=h)
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "active"

        lock_log = await db["audit_logs"].find_one({"event_code": "STUDENT_LOCK"})
        assert lock_log is not None
        unlock_log = await db["audit_logs"].find_one({"event_code": "STUDENT_UNLOCK"})
        assert unlock_log is not None


@pytest.mark.asyncio
async def test_e2e_admin_account_lifecycle():
    """System admin tạo admin thường → admin thường bị chặn ở system admin routes → vô hiệu hóa"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sys_token = await admin_login_token(client)
        sh = auth(sys_token)

        res = await client.post(
            "/api/admin/admins",
            headers=sh,
            json={
                "username": REGULAR_ADMIN_USER,
                "password": REGULAR_ADMIN_PASS,
                "display_name": "Admin Thường",
            },
        )
        assert res.status_code == 201
        regular_id = res.json()["data"]["id"]
        assert res.json()["data"]["is_system_admin"] is False

        reg_token = await admin_login_token(client, REGULAR_ADMIN_USER, REGULAR_ADMIN_PASS)
        rh = auth(reg_token)

        res = await client.get("/api/admin/auth/me", headers=rh)
        assert res.status_code == 200

        res = await client.get("/api/admin/dashboard/stats", headers=rh)
        assert res.status_code == 200

        res = await client.get("/api/admin/admins", headers=rh)
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "ADMIN_FORBIDDEN"

        res = await client.patch(f"/api/admin/admins/{regular_id}/disable", headers=sh)
        assert res.status_code == 204

        res = await client.get("/api/admin/auth/me", headers=rh)
        assert_error(res, 401, "AUTH_UNAUTHORIZED")


@pytest.mark.asyncio
async def test_e2e_admin_place_hide_and_delete():
    """Admin ẩn → bỏ ẩn → xóa mềm địa điểm"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        public_id = await seed_place(cat_id, sid)
        token = await admin_login_token(client)
        h = auth(token)

        res = await client.get(f"/api/admin/places/{public_id}", headers=h)
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "published"

        res = await client.patch(
            f"/api/admin/places/{public_id}/hide",
            headers=h,
            json={
                "hidden_note": "Vi phạm nội quy cộng đồng sử dụng hệ thống",
            },
        )
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "hidden"

        res = await client.patch(f"/api/admin/places/{public_id}/unhide", headers=h)
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "published"

        res = await client.delete(f"/api/admin/places/{public_id}", headers=h)
        assert res.status_code == 204

        db = get_db()
        place = await db["places"].find_one({"public_id": public_id})
        assert place["status"] == "deleted"
        assert place["deleted_at"] is not None


@pytest.mark.asyncio
async def test_e2e_admin_comment_soft_delete():
    """Admin xóa mềm bình luận"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        public_id = await seed_place(cat_id, sid)
        token = await admin_login_token(client)
        h = auth(token)

        db = get_db()
        now = datetime.utcnow()
        comment_res = await db["comments"].insert_one(
            {
                "place_public_id": public_id,
                "student_id": sid,
                "author_display_name": "E2E Student",
                "content": "E2E_Bình luận vi phạm nội quy cộng đồng",
                "status": "visible",
                "created_at": now,
                "updated_at": now,
            }
        )
        comment_id = str(comment_res.inserted_id)

        res = await client.get(f"/api/admin/comments?place_public_id={public_id}", headers=h)
        assert res.status_code == 200
        assert res.json()["meta"]["total"] >= 1

        res = await client.request(
            "DELETE",
            f"/api/admin/comments/{comment_id}",
            headers=h,
            json={
                "admin_delete_reason": "Vi phạm nội quy cộng đồng sử dụng hệ thống",
            },
        )
        assert res.status_code == 204

        comment = await db["comments"].find_one({"_id": comment_res.inserted_id})
        assert comment["status"] == "deleted"
        assert comment["admin_delete_reason"] == "Vi phạm nội quy cộng đồng sử dụng hệ thống"

        audit = await db["audit_logs"].find_one({"event_code": "COMMENT_ADMIN_SOFT_DELETE"})
        assert audit is not None
