from datetime import datetime

import pytest
from bson import ObjectId

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


async def _seed_report(student_id, place_public_id, report_code="E2E-RP-001"):
    db = get_db()
    now = datetime.utcnow()
    result = await db["reports"].insert_one({
        "report_code": report_code,
        "reporter_student_id": student_id,
        "target_type": "place",
        "target_place_id": ObjectId(),
        "target_comment_id": None,
        "place_public_id": place_public_id,
        "report_type": "inappropriate",
        "reason": "E2E nội dung vi phạm quy định cộng đồng",
        "status": "new",
        "admin_note": None,
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    })
    return result.inserted_id


@pytest.mark.asyncio
async def test_e2e_report_full_lifecycle():
    """new → in_progress → resolved, audit trail đầy đủ"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        pid = await seed_place(cat_id, sid)
        rid = await _seed_report(sid, pid)
        token = await admin_login_token(client)
        h = auth(token)

        res = await client.get("/api/admin/reports", headers=h)
        assert res.status_code == 200
        assert res.json()["meta"]["total"] >= 1

        res = await client.get(f"/api/admin/reports/{rid}", headers=h)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] == "new"
        assert data["report_code"] == "E2E-RP-001"

        res = await client.patch(f"/api/admin/reports/{rid}", headers=h, json={
            "status": "in_progress",
        })
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "in_progress"

        res = await client.patch(f"/api/admin/reports/{rid}", headers=h, json={
            "status": "resolved",
        })
        assert_error(res, 400, "ADMIN_NOTE_REQUIRED")

        res = await client.patch(f"/api/admin/reports/{rid}", headers=h, json={
            "status": "resolved",
            "admin_note": "Đã xác minh và xử lý vi phạm nội dung",
        })
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "resolved"
        assert res.json()["data"]["resolved_at"] is not None

        db = get_db()
        update_logs = await db["audit_logs"].find({"event_code": "REPORT_UPDATE"}).to_list(10)
        assert len(update_logs) >= 2


@pytest.mark.asyncio
async def test_e2e_report_invalid_skip_status():
    """Không cho nhảy new → resolved"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        pid = await seed_place(cat_id, sid)
        rid = await _seed_report(sid, pid, report_code="E2E-RP-002")
        token = await admin_login_token(client)

        res = await client.patch(f"/api/admin/reports/{rid}", headers=auth(token), json={
            "status": "resolved",
            "admin_note": "Bỏ qua bước xử lý vi phạm nội dung",
        })
        assert_error(res, 400, "REPORT_INVALID_STATUS")


@pytest.mark.asyncio
async def test_e2e_report_action_hide_place():
    """Thực thi hành động ẩn địa điểm từ báo cáo"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        pid = await seed_place(cat_id, sid, name="E2E_Place bị report")
        rid = await _seed_report(sid, pid, report_code="E2E-RP-003")
        token = await admin_login_token(client)
        h = auth(token)

        res = await client.post(f"/api/admin/reports/{rid}/action", headers=h, json={
            "action": "hide_place",
            "reason": "Vi phạm nội quy cộng đồng sử dụng hệ thống",
        })
        assert res.status_code == 200

        db = get_db()
        place = await db["places"].find_one({"public_id": pid})
        assert place["status"] == "hidden"


@pytest.mark.asyncio
async def test_e2e_report_action_soft_delete_comment():
    """Thực thi hành động xóa mềm bình luận từ báo cáo"""
    async with api_client() as client:
        await clean_admin_e2e_db()
        await seed_system_admin()
        sid = await seed_active_student()
        cat_id = await seed_category()
        pid = await seed_place(cat_id, sid)
        token = await admin_login_token(client)
        h = auth(token)

        db = get_db()
        now = datetime.utcnow()
        comment_res = await db["comments"].insert_one({
            "place_public_id": pid,
            "student_id": sid,
            "author_display_name": "E2E Student",
            "content": "E2E_Bình luận vi phạm nghiêm trọng",
            "status": "visible",
            "created_at": now,
            "updated_at": now,
        })
        comment_id = comment_res.inserted_id

        report_res = await db["reports"].insert_one({
            "report_code": "E2E-RP-COMMENT",
            "reporter_student_id": sid,
            "target_type": "comment",
            "target_place_id": None,
            "target_comment_id": comment_id,
            "place_public_id": pid,
            "report_type": "inappropriate",
            "reason": "E2E bình luận vi phạm nghiêm trọng",
            "status": "new",
            "admin_note": None,
            "resolved_at": None,
            "created_at": now,
            "updated_at": now,
        })
        rid = report_res.inserted_id

        res = await client.post(f"/api/admin/reports/{rid}/action", headers=h, json={
            "action": "soft_delete_comment",
            "reason": "Bình luận vi phạm nội quy cộng đồng sử dụng",
        })
        assert res.status_code == 200

        comment = await db["comments"].find_one({"_id": comment_id})
        assert comment["status"] == "deleted"
        assert comment["admin_delete_reason"] == "Bình luận vi phạm nội quy cộng đồng sử dụng"
