from datetime import datetime

import pytest

from app.api.routes.student.me import format_student_profile

pytestmark = pytest.mark.unit


def test_format_student_profile_active_with_activation_time():
    activated = datetime(2026, 5, 22, 10, 30, 0)
    student = {
        "email": "4901104172@student.hcmue.edu.vn",
        "full_name": "Nguyễn Văn A",
        "status": "active",
        "activated_at": activated,
        "locked_reason": None,
    }
    profile = format_student_profile(student)
    assert profile["status_label"] == "Đã kích hoạt"
    assert profile["activated_at_display"] == "22/05/2026 17:30"


def test_format_student_profile_pending():
    student = {
        "email": "4901104172@student.hcmue.edu.vn",
        "full_name": "Nguyễn Văn A",
        "status": "pending_activation",
        "locked_reason": None,
    }
    profile = format_student_profile(student)
    assert profile["status_label"] == "Chưa kích hoạt"
    assert profile["activated_at_display"] is None


def test_format_student_profile_locked():
    student = {
        "email": "4901104172@student.hcmue.edu.vn",
        "full_name": "Nguyễn Văn A",
        "status": "locked",
        "locked_reason": "Vi phạm quy chế",
    }
    profile = format_student_profile(student)
    assert profile["status_label"] == "Bị khóa"
    assert profile["locked_reason"] == "Vi phạm quy chế"
