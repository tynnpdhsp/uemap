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
async def test_map_config_read_and_update():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.get("/api/admin/config/map", headers=h)
        assert res.status_code == 200

        res = await client.patch(
            "/api/admin/config/map",
            headers=h,
            json={
                "default_zoom": 16,
                "default_center": {"lat": 10.77, "lng": 106.69},
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["default_zoom"] == 16
        assert data["default_center"]["lat"] == 10.77


@pytest.mark.asyncio
async def test_email_templates_read_and_update():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.get("/api/admin/config/email-templates", headers=h)
        assert res.status_code == 200

        res = await client.patch(
            "/api/admin/config/email-templates",
            headers=h,
            json={
                "activation": {
                    "subject": "Kích hoạt tài khoản",
                    "html_body": "<p>Xin chào {full_name}, mã: {otp_code}</p>",
                    "text_body": "Xin chào {full_name}, mã: {otp_code}",
                },
            },
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["activation"]["subject"] == "Kích hoạt tài khoản"


@pytest.mark.asyncio
async def test_email_templates_missing_placeholder():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.patch(
            "/api/admin/config/email-templates",
            headers=h,
            json={
                "activation": {
                    "subject": "Bad template",
                    "html_body": "<p>Không có placeholder</p>",
                    "text_body": "Không có",
                },
            },
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_config_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/config/map")
        assert res.status_code == 403
