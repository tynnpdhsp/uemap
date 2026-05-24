from app.services.audit_service import log_event as log_event
from app.services.auth_service import (
    activate_student_account as activate_student_account,
    change_password as change_password,
    login_student as login_student,
    logout_student as logout_student,
    register_student as register_student,
    request_forgot_password as request_forgot_password,
    reset_password_with_token as reset_password_with_token,
    verify_forgot_password_otp as verify_forgot_password_otp,
)
from app.services.email_service import send_otp_email as send_otp_email
from app.services.otp_service import create_otp as create_otp
from app.services.otp_service import verify_otp as verify_otp
from app.services.session_service import (
    create_session as create_session,
    revoke_all_sessions as revoke_all_sessions,
    revoke_other_sessions as revoke_other_sessions,
    revoke_session as revoke_session,
    verify_session as verify_session,
)
from app.services.geofence_service import validate_point as validate_point
from app.services.upload_service import upload_image as upload_image, upload_video as upload_video, confirm_media_keys as confirm_media_keys
from app.services.media_service import get_media_stream as get_media_stream
from app.services.place_service import create_place as create_place, update_place as update_place, delete_place as delete_place
from app.services.comment_service import create_comment as create_comment, update_comment as update_comment, delete_comment as delete_comment
from app.services.report_service import create_report as create_report
from app.services.search_service import search_places as search_places
