import uuid
from io import BytesIO
from typing import List, Optional, Tuple
from app.core.minio_client import minio_client

async def upload_image(file_data: bytes, filename: str, content_type: str, student_id: str) -> str:
    ext = filename.split(".")[-1] if "." in filename else "jpg"
    object_key = f"uploads/{student_id}/img-{uuid.uuid4()}.{ext}"
    data = BytesIO(file_data)
    await minio_client.put_object(object_key, data, len(file_data), content_type)
    return object_key

async def upload_video(file_data: bytes, filename: str, content_type: str, student_id: str) -> str:
    ext = filename.split(".")[-1] if "." in filename else "mp4"
    object_key = f"uploads/{student_id}/vid-{uuid.uuid4()}.{ext}"
    data = BytesIO(file_data)
    await minio_client.put_object(object_key, data, len(file_data), content_type)
    return object_key

async def confirm_media_keys(
    image_keys: List[str],
    video_key: Optional[str],
    public_id: int
) -> Tuple[List[str], Optional[str]]:
    new_image_keys = []
    for key in image_keys:
        if key.startswith("uploads/"):
            parts = key.split("/")
            filename = parts[-1]
            new_key = f"places/{public_id}/{filename}"
            try:
                await minio_client.copy_object(key, new_key)
                await minio_client.remove_object(key)
                new_image_keys.append(new_key)
            except Exception:
                new_image_keys.append(key)
        else:
            new_image_keys.append(key)

    new_video_key = None
    if video_key:
        if video_key.startswith("uploads/"):
            parts = video_key.split("/")
            filename = parts[-1]
            new_key = f"places/{public_id}/{filename}"
            try:
                await minio_client.copy_object(video_key, new_key)
                await minio_client.remove_object(video_key)
                new_video_key = new_key
            except Exception:
                new_video_key = video_key
        else:
            new_video_key = video_key

    return new_image_keys, new_video_key
