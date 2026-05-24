from app.services.audit_service import log_event as log_event
from app.services.auth_service import (
    activate_student_account as activate_student_account,
)
from app.services.auth_service import (
    change_password as change_password,
)
from app.services.auth_service import (
    login_student as login_student,
)
from app.services.auth_service import (
    logout_student as logout_student,
)
from app.services.auth_service import (
    register_student as register_student,
)
from app.services.auth_service import (
    request_forgot_password as request_forgot_password,
)
from app.services.auth_service import (
    reset_password_with_token as reset_password_with_token,
)
from app.services.auth_service import (
    verify_forgot_password_otp as verify_forgot_password_otp,
)
from app.services.email_service import send_otp_email as send_otp_email
from app.services.otp_service import create_otp as create_otp
from app.services.otp_service import verify_otp as verify_otp
from app.services.session_service import (
    create_session as create_session,
)
from app.services.session_service import (
    revoke_all_sessions as revoke_all_sessions,
)
from app.services.session_service import (
    revoke_other_sessions as revoke_other_sessions,
)
from app.services.session_service import (
    revoke_session as revoke_session,
)
from app.services.session_service import (
    verify_session as verify_session,
)
