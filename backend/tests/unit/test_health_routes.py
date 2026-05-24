import pytest

from app.api.routes.public.health import health_check

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_health_check_returns_ok():
    response = await health_check()
    assert response == {"success": True, "data": {"status": "ok"}}
