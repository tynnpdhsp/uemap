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
