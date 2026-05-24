import os

import pytest_asyncio

from app.core.config import settings
from app.core.database import close_db, connect_db

if not os.getenv("MONGODB_URI"):
    settings.MONGODB_URI = "mongodb://localhost:27017"


@pytest_asyncio.fixture(autouse=True)
async def db_setup():
    await connect_db()
    yield
    await close_db()
