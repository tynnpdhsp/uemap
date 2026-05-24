from typing import Optional

from fastapi import HTTPException, status

from app.core.database import get_db
from app.core.minio_client import minio_client


async def get_media_stream(object_key: str, current_student: Optional[dict] = None):
    is_allowed = False

    if object_key.startswith("places/"):
        parts = object_key.split("/")
        if len(parts) >= 2:
            try:
                public_id = int(parts[1])
                db = get_db()
                place = await db["places"].find_one({"public_id": public_id})
                if place:
                    if place["status"] == "published":
                        is_allowed = True
                    elif current_student and place["creator_student_id"] == current_student["_id"]:
                        is_allowed = True
            except ValueError:
                pass

    elif object_key.startswith("uploads/"):
        parts = object_key.split("/")
        if len(parts) >= 2:
            student_id_str = parts[1]
            if current_student and str(current_student["_id"]) == student_id_str:
                is_allowed = True

    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_NOT_FOUND",
                    "message": "Không tìm thấy tệp tin phương tiện yêu cầu hoặc không có quyền truy cập.",
                    "details": [],
                },
            },
        )

    try:
        data_stream = await minio_client.get_object(object_key)
        return data_stream
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_NOT_FOUND",
                    "message": "Tệp tin không tồn tại trên bộ lưu trữ.",
                    "details": [],
                },
            },
        )
