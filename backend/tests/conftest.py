import os

import pytest_asyncio

from app.core.config import settings
from app.core.database import close_db, connect_db

if not os.getenv("MONGODB_URI"):
    settings.MONGODB_URI = "mongodb://localhost:27017"


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests with mocked MongoDB (no real database).")
    config.addinivalue_line(
        "markers",
        "integration: API tests against real MongoDB (requires running instance).",
    )


@pytest_asyncio.fixture(autouse=True)
async def db_setup(request):
    if request.node.get_closest_marker("integration") is None:
        yield
        return
    await connect_db()
    yield
    await close_db()
