from datetime import datetime
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.database import get_db
from app.core.security import hash_password

TEST_EMAIL = "4901104172@student.hcmue.edu.vn"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Nguyễn Văn A"


async def clean_db():
    db = get_db()
    await db["students"].delete_many({"email": TEST_EMAIL})
    await db["student_sessions"].delete_many({})


@pytest.mark.asyncio
async def test_profile_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await clean_db()

        db = get_db()
        await db["students"].insert_one({
            "email": TEST_EMAIL,
            "password_hash": hash_password(TEST_PASSWORD),
            "full_name": TEST_NAME,
            "status": "active",
            "created_at": datetime.utcnow()
        })

        login_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        res = await client.post("/api/auth/login", json=login_payload)
        token = res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = await client.get("/api/me", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["email"] == TEST_EMAIL
        assert data["data"]["full_name"] == TEST_NAME
        assert data["data"]["status"] == "active"
        assert data["data"]["status_label"] == "Đã kích hoạt"

        new_name = "Nguyễn Văn B"
        res = await client.patch("/api/me", headers=headers, json={"full_name": new_name})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["full_name"] == new_name

        change_pw_payload = {
            "current_password": TEST_PASSWORD,
            "password": "newsecurepassword123",
            "password_confirm": "newsecurepassword123"
        }
        res = await client.post("/api/me/change-password", headers=headers, json=change_pw_payload)
        assert res.status_code == 200
        assert res.json()["success"] is True

        login_payload["password"] = "newsecurepassword123"
        res = await client.post("/api/auth/login", json=login_payload)
        assert res.status_code == 200
        assert res.json()["success"] is True
