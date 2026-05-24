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
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end API flows through FastAPI with real MongoDB (requires running instance).",
    )


def _needs_mongodb(request) -> bool:
    return (
        request.node.get_closest_marker("integration") is not None
        or request.node.get_closest_marker("e2e") is not None
    )


@pytest_asyncio.fixture(autouse=True)
async def db_setup(request):
    if not _needs_mongodb(request):
        yield
        return
    await connect_db()
    yield
    await close_db()
