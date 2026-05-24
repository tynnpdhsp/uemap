import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from tests.integration.admin_helpers import (
    admin_login,
    auth,
    clean_admin_db,
    seed_system_admin,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_admin_account_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.post("/api/admin/admins", headers=h, json={
            "username": "testnewadmin",
            "password": "newadminpass123",
            "display_name": "Admin Mới",
        })
        assert res.status_code == 201
        new_admin = res.json()["data"]
        new_id = new_admin["id"]
        assert new_admin["username"] == "testnewadmin"
        assert new_admin["is_system_admin"] is False

        res = await client.get("/api/admin/admins", headers=h)
        assert res.status_code == 200
        assert len(res.json()["data"]) >= 2

        res = await client.patch(f"/api/admin/admins/{new_id}", headers=h, json={
            "display_name": "Admin Cập Nhật",
        })
        assert res.status_code == 200
        assert res.json()["data"]["display_name"] == "Admin Cập Nhật"

        res = await client.patch(f"/api/admin/admins/{new_id}/disable", headers=h)
        assert res.status_code == 204


@pytest.mark.asyncio
async def test_admin_cannot_self_disable():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        admin_id = await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.patch(f"/api/admin/admins/{admin_id}/disable", headers=h)
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "ADMIN_CANNOT_DISABLE_SELF"


@pytest.mark.asyncio
async def test_admin_duplicate_username():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        await client.post("/api/admin/admins", headers=h, json={
            "username": "testdup", "password": "password12345", "display_name": "Dup",
        })
        res = await client.post("/api/admin/admins", headers=h, json={
            "username": "testdup", "password": "password12345", "display_name": "Dup 2",
        })
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "ADMIN_USERNAME_EXISTS"


@pytest.mark.asyncio
async def test_admin_accounts_require_system_admin():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.post("/api/admin/admins", headers=h, json={
            "username": "testregular", "password": "password12345", "display_name": "Regular",
        })
        assert res.status_code == 201

        res = await client.post("/api/admin/auth/login", json={
            "username": "testregular", "password": "password12345",
        })
        regular_token = res.json()["data"]["access_token"]
        rh = auth(regular_token)

        res = await client.get("/api/admin/admins", headers=rh)
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "ADMIN_FORBIDDEN"
