import pytest
from pydantic import ValidationError

from app.schemas.student import ChangePasswordRequest, StudentProfileUpdateRequest

pytestmark = pytest.mark.unit


def test_profile_update_trims_full_name():
    req = StudentProfileUpdateRequest(full_name="  Nguyễn   Văn   A  ")
    assert req.full_name == "Nguyễn Văn A"


def test_profile_update_rejects_short_name():
    with pytest.raises(ValidationError):
        StudentProfileUpdateRequest(full_name="ABC")


def test_change_password_request_valid():
    req = ChangePasswordRequest(
        current_password="oldpass12",
        password="newpass123",
        password_confirm="newpass123",
    )
    assert req.password == "newpass123"


def test_change_password_mismatch():
    with pytest.raises(ValidationError):
        ChangePasswordRequest(
            current_password="oldpass12",
            password="newpass123",
            password_confirm="different",
        )
