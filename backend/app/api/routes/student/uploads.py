from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from app.api.deps import require_active_student
from app.services import upload_service
from app.schemas.upload import UploadImagesResponse, UploadMediaResponse

router = APIRouter()

@router.post("/images", response_model=UploadImagesResponse, status_code=status.HTTP_201_CREATED)
async def upload_student_images(
    files: List[UploadFile] = File(...),
    current_student: dict = Depends(require_active_student)
):
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Chỉ được phép tải lên tối đa 10 ảnh.",
                    "details": []
                }
            }
        )

    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    max_size = 5 * 1024 * 1024
    
    object_keys = []
    preview_urls = []

    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "FILE_TYPE_INVALID",
                        "message": f"Tệp {file.filename} không đúng định dạng ảnh (chỉ chấp nhận JPEG, PNG, WebP).",
                        "details": []
                    }
                }
            )

        file_bytes = await file.read()
        if len(file_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": {
                        "code": "FILE_SIZE_EXCEEDED",
                        "message": f"Tệp {file.filename} vượt quá giới hạn 5 MB.",
                        "details": []
                    }
                }
            )

        key = await upload_service.upload_image(
            file_data=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            student_id=str(current_student["_id"])
        )
        object_keys.append(key)
        preview_urls.append(f"/api/media/{key}")

    return {
        "object_keys": object_keys,
        "preview_urls": preview_urls
    }

@router.post("/video", response_model=UploadMediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_student_video(
    file: UploadFile = File(...),
    current_student: dict = Depends(require_active_student)
):
    allowed_types = ["video/mp4", "video/webm"]
    max_size = 80 * 1024 * 1024

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "FILE_TYPE_INVALID",
                    "message": "Chỉ chấp nhận tệp tin video định dạng MP4 hoặc WebM.",
                    "details": []
                }
            }
        )

    file_bytes = await file.read()
    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": {
                    "code": "FILE_SIZE_EXCEEDED",
                    "message": "Tệp tin video vượt quá giới hạn dung lượng 80 MB.",
                    "details": []
                }
            }
        )

    key = await upload_service.upload_video(
        file_data=file_bytes,
        filename=file.filename,
        content_type=file.content_type,
        student_id=str(current_student["_id"])
    )

    return {
        "object_key": key,
        "preview_url": f"/api/media/{key}"
    }
