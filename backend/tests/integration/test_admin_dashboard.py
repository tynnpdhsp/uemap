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
async def test_dashboard_stats():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)

        res = await client.get("/api/admin/dashboard/stats", headers=auth(token))
        assert res.status_code == 200
        data = res.json()["data"]
        assert "new_reports_count" in data
        assert "pending_students_7d_count" in data
        assert "new_published_places_7d_count" in data
        assert "links" in data


@pytest.mark.asyncio
async def test_dashboard_stats_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/dashboard/stats")
        assert res.status_code == 403
