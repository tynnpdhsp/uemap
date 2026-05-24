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
async def test_category_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.post("/api/admin/categories", headers=h, json={
            "name": "IntTest Ăn uống", "color": "#FF0000", "order": 0,
        })
        assert res.status_code == 201
        cat = res.json()["data"]
        cat_id = cat["id"]
        assert cat["name"] == "IntTest Ăn uống"

        res = await client.get("/api/admin/categories", headers=h)
        assert res.status_code == 200
        names = [c["name"] for c in res.json()["data"]]
        assert "IntTest Ăn uống" in names

        res = await client.patch(f"/api/admin/categories/{cat_id}", headers=h, json={
            "name": "IntTest Giải trí",
        })
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "IntTest Giải trí"

        res = await client.patch(f"/api/admin/categories/{cat_id}/hide", headers=h, json={
            "is_hidden": True,
        })
        assert res.status_code == 200
        assert res.json()["data"]["is_hidden"] is True

        res = await client.delete(f"/api/admin/categories/{cat_id}", headers=h)
        assert res.status_code == 204


@pytest.mark.asyncio
async def test_category_create_duplicate_name():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        await client.post("/api/admin/categories", headers=h, json={
            "name": "IntTest Duplicate", "color": "#00FF00",
        })
        res = await client.post("/api/admin/categories", headers=h, json={
            "name": "IntTest Duplicate", "color": "#0000FF",
        })
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "CATEGORY_NAME_EXISTS"


@pytest.mark.asyncio
async def test_category_delete_with_places_conflict():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_admin_db()
        await seed_system_admin()
        token = await admin_login(client)
        h = auth(token)

        res = await client.post("/api/admin/categories", headers=h, json={
            "name": "IntTest HasPlaces", "color": "#FF0000",
        })
        cat_id = res.json()["data"]["id"]

        from bson import ObjectId
        db = get_db()
        await db["places"].insert_one({
            "name": "IntTest Place",
            "category_id": ObjectId(cat_id),
            "status": "published",
        })

        res = await client.delete(f"/api/admin/categories/{cat_id}", headers=h)
        assert res.status_code == 409
        assert res.json()["error"]["code"] == "CATEGORY_DELETE_HAS_PLACES"


@pytest.mark.asyncio
async def test_category_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/admin/categories")
        assert res.status_code == 403
