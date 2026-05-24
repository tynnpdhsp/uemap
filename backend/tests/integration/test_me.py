from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.services import session_service
from tests.auth_integration_helpers import (
    TEST_EMAIL,
    TEST_NAME,
    TEST_PASSWORD,
    clean_auth_integration_db,
)

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_profile_view_and_update():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        db = get_db()
        await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "active",
                "created_at": datetime.utcnow(),
            }
        )

        login_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        res = await client.post("/api/auth/login", json=login_payload)
        token = res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.get("/api/me", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["email"] == TEST_EMAIL

        new_name = "Nguyễn Văn B"
        res = await client.patch("/api/me", headers=headers, json={"full_name": new_name})
        assert res.status_code == 200
        assert res.json()["data"]["full_name"] == new_name

        res = await client.patch("/api/me", headers=headers, json={"full_name": "ABC"})
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_change_password_scenarios():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        db = get_db()
        await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "active",
                "created_at": datetime.utcnow(),
            }
        )

        login_payload = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
        res = await client.post("/api/auth/login", json=login_payload)
        token = res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "current_password": "wrongcurrentpassword",
            "password": "newsecurepassword123",
            "password_confirm": "newsecurepassword123",
        }
        res = await client.post("/api/me/change-password", headers=headers, json=payload)
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "AUTH_PASSWORD_CHANGE_FAILED"

        payload["current_password"] = TEST_PASSWORD
        payload["password_confirm"] = "differentconfirm"
        res = await client.post("/api/me/change-password", headers=headers, json=payload)
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_locked_student_profile_access():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_auth_integration_db()

        db = get_db()
        student_res = await db["students"].insert_one(
            {
                "email": TEST_EMAIL,
                "password_hash": hash_password(TEST_PASSWORD),
                "full_name": TEST_NAME,
                "status": "locked",
                "locked_reason": "Vi phạm quy chế hệ thống",
                "created_at": datetime.utcnow(),
            }
        )
        student_id = student_res.inserted_id

        token = await session_service.create_session(student_id, "127.0.0.1", "Mozilla/5.0")
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.get("/api/me", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["status"] == "locked"
        assert data["data"]["status_label"] == "Bị khóa"
        assert data["data"]["locked_reason"] == "Vi phạm quy chế hệ thống"

        new_name = "Nguyễn Văn Locked"
        res = await client.patch("/api/me", headers=headers, json={"full_name": new_name})
        assert res.status_code == 200
        assert res.json()["data"]["full_name"] == new_name
