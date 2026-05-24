import pytest
from fastapi import HTTPException

from app.main import http_exception_handler

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_http_exception_handler_preserves_structured_detail():
    exc = HTTPException(
        status_code=400,
        detail={
            "success": False,
            "error": {"code": "AUTH_EMAIL_EXISTS", "message": "Email đã tồn tại.", "details": []},
        },
    )
    response = await http_exception_handler(None, exc)
    assert response.status_code == 400
    body = response.body.decode()
    assert "AUTH_EMAIL_EXISTS" in body


@pytest.mark.asyncio
async def test_http_exception_handler_wraps_plain_detail():
    exc = HTTPException(status_code=500, detail="Internal error")
    response = await http_exception_handler(None, exc)
    assert response.status_code == 500
    body = response.body.decode()
    assert "HTTP_ERROR" in body
