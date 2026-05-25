import pytest

from app.core.database import get_db
from tests.e2e.admin_e2e_helpers import (
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
async def test_e2e_config_map_full_flow():
    """Đọc → cập nhật center + zoom + geofence → đọc lại"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        token = await admin_login_token(client)
        h = auth(token)

        res = await client.get("/api/admin/config/map", headers=h)
        assert res.status_code == 200

        res = await client.patch(
            "/api/admin/config/map",
            headers=h,
            json={
                "default_center": {"lat": 10.77, "lng": 106.69},
                "default_zoom": 16,
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["default_center"]["lat"] == 10.77
        assert data["default_zoom"] == 16

        res = await client.patch(
            "/api/admin/config/map",
            headers=h,
            json={
                "geofence": {
                    "type": "rectangle",
                    "bounds": {
                        "sw": {"lat": 10.0, "lng": 106.0},
                        "ne": {"lat": 11.0, "lng": 107.0},
                    },
                },
            },
        )
        assert res.status_code == 200
        assert res.json()["data"]["geofence"]["type"] == "rectangle"

        res = await client.get("/api/admin/config/map", headers=h)
        assert res.status_code == 200
        assert res.json()["data"]["default_zoom"] == 16

        db = get_db()
        logs = await db["audit_logs"].find({"event_code": "CONFIG_MAP_UPDATE"}).to_list(10)
        assert len(logs) >= 2


@pytest.mark.asyncio
async def test_e2e_config_email_templates_flow():
    """Đọc → cập nhật → validation placeholder → đọc lại"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        token = await admin_login_token(client)
        h = auth(token)

        res = await client.get("/api/admin/config/email-templates", headers=h)
        assert res.status_code == 200

        res = await client.patch(
            "/api/admin/config/email-templates",
            headers=h,
            json={
                "activation": {
                    "subject": "Kích hoạt tài khoản E2E",
                    "html_body": "<p>Xin chào {full_name}, mã: {otp_code}</p>",
                    "text_body": "Xin chào {full_name}, mã: {otp_code}",
                },
            },
        )
        assert res.status_code == 200
        assert res.json()["data"]["activation"]["subject"] == "Kích hoạt tài khoản E2E"

        res = await client.patch(
            "/api/admin/config/email-templates",
            headers=h,
            json={
                "activation": {
                    "subject": "Bad",
                    "html_body": "<p>Không có placeholder</p>",
                    "text_body": "Không có placeholder",
                },
            },
        )
        assert_error(res, 400, "VALIDATION_ERROR")

        res = await client.get("/api/admin/config/email-templates", headers=h)
        assert res.json()["data"]["activation"]["subject"] == "Kích hoạt tài khoản E2E"


@pytest.mark.asyncio
async def test_e2e_audit_log_trail():
    """Thực hiện nhiều thao tác → audit log ghi nhận đủ, export CSV"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        await seed_place(cat_id, sid)
        token = await admin_login_token(client)
        h = auth(token)

        await client.post(
            "/api/admin/categories",
            headers=h,
            json={
                "name": "E2E_AuditTest",
                "color": "#123456",
            },
        )

        await client.patch(
            f"/api/admin/students/{sid}/lock",
            headers=h,
            json={
                "locked_reason": "E2E audit test vi phạm nội quy",
            },
        )

        res = await client.get("/api/admin/audit-logs", headers=h)
        assert res.status_code == 200
        total = res.json()["meta"]["total"]
        assert total >= 3
        res = await client.get("/api/admin/audit-logs?event_code=STUDENT_LOCK", headers=h)
        assert res.status_code == 200
        for item in res.json()["data"]:
            assert item["event_code"] == "STUDENT_LOCK"

        res = await client.get("/api/admin/audit-logs/export", headers=h)
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        content = res.text
        assert "ADMIN_LOGIN" in content
        assert "CATEGORY_CREATE" in content
        assert "STUDENT_LOCK" in content


@pytest.mark.asyncio
async def test_e2e_dashboard_reflects_data():
    """Dashboard trả stats phản ánh dữ liệu thực tế"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        await seed_place(cat_id, sid, name="E2E_Dashboard Place")
        token = await admin_login_token(client)

        db = get_db()
        from datetime import datetime

        await db["reports"].insert_one(
            {
                "report_code": "E2E-DASH-001",
                "reporter_student_id": sid,
                "target_type": "place",
                "target_place_id": None,
                "target_comment_id": None,
                "place_public_id": None,
                "report_type": "inappropriate",
                "reason": "E2E dashboard test",
                "status": "new",
                "admin_note": None,
                "resolved_at": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )

        res = await client.get("/api/admin/dashboard/stats", headers=auth(token))
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["new_reports_count"] >= 1
        assert data["new_published_places_7d_count"] >= 1
