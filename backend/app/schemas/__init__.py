from app.schemas.auth import (
    ForgotPasswordRequest as ForgotPasswordRequest,
    ForgotPasswordVerifyRequest as ForgotPasswordVerifyRequest,
    ForgotPasswordVerifyResponse as ForgotPasswordVerifyResponse,
    LoginRequest as LoginRequest,
    LoginResponse as LoginResponse,
    OTPResendRequest as OTPResendRequest,
    OTPVerifyRequest as OTPVerifyRequest,
    ResetPasswordRequest as ResetPasswordRequest,
    StudentRegisterRequest as StudentRegisterRequest,
    StudentRegisterResponse as StudentRegisterResponse,
)
from app.schemas.student import (
    ChangePasswordRequest as ChangePasswordRequest,
    StudentProfileResponse as StudentProfileResponse,
    StudentProfileUpdateRequest as StudentProfileUpdateRequest,
)
from app.schemas.map_config import AppConfigResponse as AppConfigResponse, MapGeofenceSchema as MapGeofenceSchema
from app.schemas.place import (
    PlaceMarkerResponse as PlaceMarkerResponse,
    PlaceListResponseItem as PlaceListResponseItem,
    PlaceDetailResponse as PlaceDetailResponse,
    PlaceCreateRequest as PlaceCreateRequest,
    PlaceCreateResponse as PlaceCreateResponse,
)
from app.schemas.comment import (
    CommentResponse as CommentResponse,
    CommentMyResponseItem as CommentMyResponseItem,
    CommentCreateRequest as CommentCreateRequest,
)
from app.schemas.report import (
    ReportCreateRequest as ReportCreateRequest,
    ReportCreateResponse as ReportCreateResponse,
    ReportMyResponseItem as ReportMyResponseItem,
)
from app.schemas.upload import (
    UploadMediaResponse as UploadMediaResponse,
    UploadImagesResponse as UploadImagesResponse,
)
from app.schemas.admin import (
    AdminLoginRequest as AdminLoginRequest,
    AdminLoginResponse as AdminLoginResponse,
    AdminInfoResponse as AdminInfoResponse,
    AdminCreateRequest as AdminCreateRequest,
    AdminUpdateRequest as AdminUpdateRequest,
)
from app.schemas.admin_category import (
    AdminCategoryCreateRequest as AdminCategoryCreateRequest,
    AdminCategoryUpdateRequest as AdminCategoryUpdateRequest,
    AdminCategoryHideRequest as AdminCategoryHideRequest,
    AdminCategoryResponse as AdminCategoryResponse,
)
from app.schemas.admin_place import (
    AdminPlaceHideRequest as AdminPlaceHideRequest,
    AdminPlaceTransferCreatorRequest as AdminPlaceTransferCreatorRequest,
    AdminPlaceUpdateRequest as AdminPlaceUpdateRequest,
)
from app.schemas.admin_report import (
    AdminReportUpdateRequest as AdminReportUpdateRequest,
    AdminReportActionRequest as AdminReportActionRequest,
)
from app.schemas.admin_config import (
    AdminMapConfigUpdateRequest as AdminMapConfigUpdateRequest,
    AdminEmailTemplatesUpdateRequest as AdminEmailTemplatesUpdateRequest,
    AdminEmailTestRequest as AdminEmailTestRequest,
)
from app.schemas.audit_log import AuditLogResponse as AuditLogResponse
