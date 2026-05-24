from unittest.mock import AsyncMock, patch
import pytest
from bson import ObjectId
from fastapi import HTTPException
from app.services import media_service

pytestmark = pytest.mark.unit

@pytest.mark.asyncio
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_get_media_stream_published_success(mock_minio, mock_db):
    place_id = ObjectId()
    await mock_db["places"].insert_one({
        "_id": place_id,
        "public_id": 100,
        "status": "published"
    })

    mock_minio.get_object.return_value = b"file-data-stream"

    result = await media_service.get_media_stream("places/100/image1.webp")
    assert result == b"file-data-stream"
    mock_minio.get_object.assert_called_once_with("places/100/image1.webp")

@pytest.mark.asyncio
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_get_media_stream_draft_owner_success(mock_minio, mock_db):
    student_id = ObjectId()
    place_id = ObjectId()
    await mock_db["places"].insert_one({
        "_id": place_id,
        "public_id": 101,
        "status": "draft",
        "creator_student_id": student_id
    })

    mock_minio.get_object.return_value = b"file-data-stream"

    result = await media_service.get_media_stream(
        "places/101/image2.webp",
        current_student={"_id": student_id}
    )
    assert result == b"file-data-stream"

@pytest.mark.asyncio
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_get_media_stream_draft_other_forbidden(mock_minio, mock_db):
    owner_id = ObjectId()
    other_id = ObjectId()
    await mock_db["places"].insert_one({
        "public_id": 102,
        "status": "draft",
        "creator_student_id": owner_id
    })

    with pytest.raises(HTTPException) as exc:
        await media_service.get_media_stream(
            "places/102/image2.webp",
            current_student={"_id": other_id}
        )
    assert exc.value.status_code == 404

@pytest.mark.asyncio
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_get_media_stream_upload_temp_owner(mock_minio, mock_db):
    student_id = ObjectId()
    mock_minio.get_object.return_value = b"temp-file"

    result = await media_service.get_media_stream(
        f"uploads/{str(student_id)}/temp1.webp",
        current_student={"_id": student_id}
    )
    assert result == b"temp-file"

@pytest.mark.asyncio
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_get_media_stream_upload_temp_other_forbidden(mock_minio, mock_db):
    owner_id = ObjectId()
    other_id = ObjectId()

    with pytest.raises(HTTPException) as exc:
        await media_service.get_media_stream(
            f"uploads/{str(owner_id)}/temp1.webp",
            current_student={"_id": other_id}
        )
    assert exc.value.status_code == 404
