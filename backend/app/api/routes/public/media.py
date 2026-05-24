import mimetypes
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from app.api.deps import decode_access_token, get_db
from app.services import session_service, media_service
from bson import ObjectId

router = APIRouter()
optional_security = HTTPBearer(auto_error=False)

async def get_optional_student(credentials=Depends(optional_security)) -> Optional[dict]:
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("role") != "student":
            return None
        jti = payload.get("jti")
        student_id_str = payload.get("sub")
        if not jti or not student_id_str:
            return None
        
        is_active_session = await session_service.verify_session(jti)
        if not is_active_session:
            return None
            
        db = get_db()
        student = await db["students"].find_one({"_id": ObjectId(student_id_str)})
        return student
    except Exception:
        return None

@router.get("/{object_key:path}")
async def get_media(
    object_key: str,
    current_student: Optional[dict] = Depends(get_optional_student)
):
    stream = await media_service.get_media_stream(object_key, current_student)
    
    mime_type, _ = mimetypes.guess_type(object_key)
    if not mime_type:
        if "vid-" in object_key:
            mime_type = "video/mp4"
        else:
            mime_type = "image/webp"

    return StreamingResponse(
        stream,
        media_type=mime_type,
        headers={"Cache-Control": "max-age=86400, public"}
    )
