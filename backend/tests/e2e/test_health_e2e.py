import pytest

from tests.e2e.helpers import api_client

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_health_endpoint_smoke():
    async with api_client() as client:
        res = await client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
