from datetime import datetime

import pytest
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from tests.integration.admin_helpers import (
    admin_login,
    auth,
    clean_admin_db,
    seed_student,
    seed_system_admin,
)

pytestmark = pytest.mark.integration


async def _seed_report(student_id: ObjectId, **overrides) -> ObjectId:
    db = get_db()
    now = datetime.utcnow()
    doc = {
        "report_code": overrides.pop("report_code", "INTEST-RP-001"),
        "reporter_student_id": student_id,
        "target_type": "place",
        "target_place_id": ObjectId(),
        "target_comment_id": None,
        "place_public_id": 1,
        "report_type": "inappropriate",
        "reason": "Nội dung không phù hợp",
        "status": "new",
        "admin_note": None,
        "resolved_at": None,
        "created_at": now,
        "updated_at": now,
    }
    doc.update(overrides)
    result = await db["reports"].insert_one(doc)
    return result.inserted_id


@pytest.mark.asyncio
async def test_list_reports():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        await _seed_report(sid, report_code="INTEST-RP-001")
        await _seed_report(sid, report_code="INTEST-RP-002")
        token = await admin_login(client)

        res = await client.get("/api/admin/reports", headers=auth(token))
        assert res.status_code == 200
        assert res.json()["meta"]["total"] >= 2


@pytest.mark.asyncio
async def test_list_reports_filter_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        await _seed_report(sid, report_code="INTEST-RP-NEW", status="new")
        await _seed_report(sid, report_code="INTEST-RP-RES", status="resolved")
        token = await admin_login(client)

        res = await client.get("/api/admin/reports?status=new", headers=auth(token))
        assert res.status_code == 200
        for item in res.json()["data"]:
            assert item["status"] == "new"


@pytest.mark.asyncio
async def test_report_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        rid = await _seed_report(sid)
        token = await admin_login(client)

        res = await client.get(f"/api/admin/reports/{rid}", headers=auth(token))
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["report_code"] == "INTEST-RP-001"
        assert data["reporter_email"] == "inttest_sv@student.hcmue.edu.vn"


@pytest.mark.asyncio
async def test_report_status_transition():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        rid = await _seed_report(sid)
        token = await admin_login(client)
        h = auth(token)

        res = await client.patch(f"/api/admin/reports/{rid}", headers=h, json={
            "status": "in_progress",
        })
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "in_progress"

        res = await client.patch(f"/api/admin/reports/{rid}", headers=h, json={
            "status": "resolved",
        })
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "ADMIN_NOTE_REQUIRED"

        res = await client.patch(f"/api/admin/reports/{rid}", headers=h, json={
            "status": "resolved",
            "admin_note": "Đã xử lý xong vi phạm nội dung",
        })
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "resolved"
        assert res.json()["data"]["resolved_at"] is not None


@pytest.mark.asyncio
async def test_report_invalid_transition():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        rid = await _seed_report(sid, status="new")
        token = await admin_login(client)

        res = await client.patch(f"/api/admin/reports/{rid}", headers=auth(token), json={
            "status": "resolved",
            "admin_note": "Bỏ qua bước đang xử lý",
        })
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "REPORT_INVALID_STATUS"
