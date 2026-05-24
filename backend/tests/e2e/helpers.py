from contextlib import asynccontextmanager, contextmanager
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app

TEST_EMAIL = "4901104172@student.hcmue.edu.vn"
TEST_PASSWORD = "testpassword123"
TEST_NEW_PASSWORD = "newsecurepassword123"
TEST_NAME = "Nguyễn Văn A"
FIXED_OTP = "111111"

REGISTER_PAYLOAD = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD,
    "password_confirm": TEST_PASSWORD,
    "full_name": TEST_NAME,
    "accept_terms": True,
}

EMAIL_PATCH_TARGET = "app.services.email_service.send_otp_email"


def _otp_digit(_a: int, _b: int) -> int:
    return 1


async def clean_auth_db() -> None:
    db = get_db()
    await db["otp_tokens"].delete_many({"email": TEST_EMAIL})
    await db["students"].delete_many({"email": TEST_EMAIL})
    await db["student_sessions"].delete_many({})
    await db["login_attempts"].delete_many({"email": TEST_EMAIL})
    await db["audit_logs"].delete_many({})


@asynccontextmanager
async def api_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@contextmanager
def mock_auth_otp_and_email():
    email_mock = AsyncMock(return_value=None)
    patches = [
        patch("app.services.otp_service.random.randint", side_effect=_otp_digit),
        patch(EMAIL_PATCH_TARGET, email_mock),
    ]
    for p in patches:
        p.start()
    try:
        yield email_mock
    finally:
        for p in patches:
            p.stop()


async def register_student(client: AsyncClient) -> None:
    res = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert res.status_code == 201, res.text
    assert res.json()["success"] is True


async def activate_account(client: AsyncClient) -> None:
    res = await client.post(
        "/api/auth/otp/verify",
        json={"email": TEST_EMAIL, "otp": FIXED_OTP, "purpose": "activation"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    assert "activated_at_display" in body["data"]


async def login(client: AsyncClient, password: str = TEST_PASSWORD) -> str:
    res = await client.post(
        "/api/auth/login",
        json={"email": TEST_EMAIL, "password": password},
    )
    assert res.status_code == 200, res.text
    return res.json()["data"]["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def assert_student_status(status: str) -> None:
    db = get_db()
    student = await db["students"].find_one({"email": TEST_EMAIL})
    assert student is not None
    assert student["status"] == status


async def setup_active_student(client: AsyncClient) -> str:
    await clean_auth_db()
    with mock_auth_otp_and_email():
        await register_student(client)
        await activate_account(client)
    return await login(client)


def assert_error(res, status_code: int, code: str) -> None:
    assert res.status_code == status_code, res.text
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == code
