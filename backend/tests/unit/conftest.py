from contextlib import contextmanager
from unittest.mock import patch

import pytest

from tests.unit.helpers.mock_db import MockDatabase

GET_DB_TARGETS = [
    "app.services.auth_service.get_db",
    "app.services.otp_service.get_db",
    "app.services.session_service.get_db",
    "app.services.audit_service.get_db",
    "app.api.deps.get_db",
    "app.api.routes.student.auth.get_db",
    "app.api.routes.student.me.get_db",
]

TEST_EMAIL = "4901104172@student.hcmue.edu.vn"
TEST_PASSWORD = "testpassword123"
TEST_NAME = "Nguyễn Văn A"


@pytest.fixture
def mock_db() -> MockDatabase:
    return MockDatabase()


@contextmanager
def use_mock_db(mock_db: MockDatabase):
    patches = [patch(target, return_value=mock_db) for target in GET_DB_TARGETS]
    for p in patches:
        p.start()
    try:
        yield
    finally:
        for p in patches:
            p.stop()


@pytest.fixture(autouse=True)
def _patch_get_db(mock_db: MockDatabase):
    with use_mock_db(mock_db):
        yield mock_db
