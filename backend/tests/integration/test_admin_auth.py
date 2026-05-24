from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from tests.integration.admin_helpers import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    admin_login,
    auth,
    clean_admin_db,
    seed_system_admin,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_admin_login_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()

        res = await client.post("/api/admin/auth/login", json={
            "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD,
        })
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert "access_token" in body["data"]
        assert body["data"]["admin"]["username"] == ADMIN_USERNAME
        assert body["data"]["admin"]["is_system_admin"] is True


@pytest.mark.asyncio
async def test_admin_login_wrong_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()

        res = await client.post("/api/admin/auth/login", json={
            "username": ADMIN_USERNAME, "password": "wrongpassword1",
        })
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "ADMIN_LOGIN_FAILED"


@pytest.mark.asyncio
async def test_admin_login_wrong_username():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()

        res = await client.post("/api/admin/auth/login", json={
            "username": "nonexistent", "password": ADMIN_PASSWORD,
        })
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "ADMIN_LOGIN_FAILED"


@pytest.mark.asyncio
async def test_admin_login_rate_limit():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()

        db = get_db()
        now = datetime.utcnow()
        for _ in range(10):
            await db["admin_login_attempts"].insert_one({
                "username": ADMIN_USERNAME, "ip_address": "127.0.0.1", "failed_at": now,
            })

        res = await client.post("/api/admin/auth/login", json={
            "username": ADMIN_USERNAME, "password": ADMIN_PASSWORD,
        })
        assert res.status_code == 429
        assert res.json()["error"]["code"] == "AUTH_LOGIN_RATE_LIMIT"


@pytest.mark.asyncio
async def test_admin_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)

        res = await client.get("/api/admin/auth/me", headers=auth(token))
        assert res.status_code == 200
        body = res.json()
        assert body["data"]["username"] == ADMIN_USERNAME


@pytest.mark.asyncio
async def test_admin_me_without_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/auth/me")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_logout():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)

        res = await client.post("/api/admin/auth/logout", headers=auth(token))
        assert res.status_code == 204

        res = await client.get("/api/admin/auth/me", headers=auth(token))
        assert res.status_code == 401
