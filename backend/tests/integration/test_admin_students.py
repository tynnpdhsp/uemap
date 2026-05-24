import pytest
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


@pytest.mark.asyncio
async def test_list_students():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        await seed_student("inttest_a@student.hcmue.edu.vn")
        await seed_student("inttest_b@student.hcmue.edu.vn")
        token = await admin_login(client)

        res = await client.get("/api/admin/students", headers=auth(token))
        assert res.status_code == 200
        assert res.json()["meta"]["total"] >= 2


@pytest.mark.asyncio
async def test_list_students_filter_email():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        await seed_student("inttest_alice@student.hcmue.edu.vn")
        await seed_student("inttest_bob@student.hcmue.edu.vn")
        token = await admin_login(client)

        res = await client.get("/api/admin/students?email=alice", headers=auth(token))
        assert res.status_code == 200
        assert res.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_student_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        token = await admin_login(client)

        res = await client.get(f"/api/admin/students/{sid}", headers=auth(token))
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["email"] == "inttest_sv@student.hcmue.edu.vn"
        assert data["status"] == "active"
        assert "places_count" in data


@pytest.mark.asyncio
async def test_lock_and_unlock_student():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        token = await admin_login(client)
        h = auth(token)

        res = await client.patch(f"/api/admin/students/{sid}/lock", headers=h, json={
            "locked_reason": "Vi phạm quy định sử dụng hệ thống",
        })
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "locked"

        db = get_db()
        student = await db["students"].find_one({"_id": sid})
        assert student["status"] == "locked"

        res = await client.patch(f"/api/admin/students/{sid}/unlock", headers=h)
        assert res.status_code == 200
        assert res.json()["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_lock_student_revokes_sessions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        sid = await seed_student()
        token = await admin_login(client)
        h = auth(token)

        from datetime import datetime, timedelta
        db = get_db()
        await db["student_sessions"].insert_one({
            "student_id": sid, "jti": "inttest-jti-1", "revoked_at": None,
            "expires_at": datetime.utcnow() + timedelta(days=7),
        })

        await client.patch(f"/api/admin/students/{sid}/lock", headers=h, json={
            "locked_reason": "Vi phạm quy định sử dụng hệ thống",
        })

        session = await db["student_sessions"].find_one({"jti": "inttest-jti-1"})
        assert session["revoked_at"] is not None
