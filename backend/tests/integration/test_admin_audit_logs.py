import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.integration.admin_helpers import (
    admin_login,
    auth,
    clean_admin_db,
    seed_system_admin,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_audit_logs_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)

        res = await client.get("/api/admin/audit-logs", headers=auth(token))
        assert res.status_code == 200
        body = res.json()
        assert body["meta"]["total"] >= 1
        assert len(body["data"]) >= 1

        item = body["data"][0]
        assert "event_code" in item
        assert "occurred_at_display" in item
        assert "ip_address" in item


@pytest.mark.asyncio
async def test_audit_logs_filter_event_code():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)

        res = await client.get("/api/admin/audit-logs?event_code=ADMIN_LOGIN", headers=auth(token))
        assert res.status_code == 200
        for item in res.json()["data"]:
            assert item["event_code"] == "ADMIN_LOGIN"


@pytest.mark.asyncio
async def test_audit_logs_export_csv():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)

        res = await client.get("/api/admin/audit-logs/export", headers=auth(token))
        assert res.status_code == 200
        assert "text/csv" in res.headers["content-type"]
        assert "attachment" in res.headers.get("content-disposition", "")
        content = res.text
        assert "Mã sự kiện" in content


@pytest.mark.asyncio
async def test_audit_logs_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/audit-logs")
        assert res.status_code == 403
