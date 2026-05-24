from app.services.audit_service import log_event
from app.services.email_service import send_otp_email
from app.services.otp_service import create_otp, verify_otp
from app.services.session_service import (
    create_session,
    verify_session,
    revoke_session,
    revoke_all_sessions,
    revoke_other_sessions,
)
from app.services.auth_service import (
    register_student,
    activate_student_account,
    login_student,
    logout_student,
    request_forgot_password,
    verify_forgot_password_otp,
    reset_password_with_token,
    change_password,
)
