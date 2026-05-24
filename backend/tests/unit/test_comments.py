import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.services import comment_service

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_create_comment_success(mock_db):
    place_id = ObjectId()
    await mock_db["places"].insert_one(
        {"_id": place_id, "public_id": 1, "status": "published", "name": "Quán ngon"}
    )

    student_id = ObjectId()
    student_name = "Nguyễn Văn A"

    result = await comment_service.create_comment(
        place_public_id=1,
        student_id=student_id,
        student_name=student_name,
        content="Bình luận thử nghiệm",
        ip_address="127.0.0.1",
    )

    assert result["author_display_name"] == student_name
    assert result["content"] == "Bình luận thử nghiệm"
    assert "id" in result

    db_comment = await mock_db["comments"].find_one({"_id": ObjectId(result["id"])})
    assert db_comment is not None
    assert db_comment["status"] == "visible"
    assert db_comment["place_id"] == place_id


@pytest.mark.asyncio
async def test_create_comment_on_draft_fails(mock_db):
    await mock_db["places"].insert_one({"public_id": 2, "status": "draft", "name": "Quán nháp"})

    student_id = ObjectId()
    with pytest.raises(HTTPException) as exc:
        await comment_service.create_comment(
            place_public_id=2,
            student_id=student_id,
            student_name="Sinh viên",
            content="Lỗi nè",
            ip_address="127.0.0.1",
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error"]["code"] == "COMMENT_FORBIDDEN"


@pytest.mark.asyncio
async def test_update_comment_success(mock_db):
    student_id = ObjectId()
    comment_id = ObjectId()
    await mock_db["comments"].insert_one(
        {"_id": comment_id, "student_id": student_id, "content": "Nội dung cũ", "status": "visible"}
    )

    await comment_service.update_comment(
        comment_id=str(comment_id),
        student_id=student_id,
        content="Nội dung mới",
        ip_address="127.0.0.1",
    )

    db_comment = await mock_db["comments"].find_one({"_id": comment_id})
    assert db_comment["content"] == "Nội dung mới"


@pytest.mark.asyncio
async def test_update_comment_forbidden(mock_db):
    owner_id = ObjectId()
    other_id = ObjectId()
    comment_id = ObjectId()
    await mock_db["comments"].insert_one(
        {
            "_id": comment_id,
            "student_id": owner_id,
            "content": "Không được sửa đâu",
            "status": "visible",
        }
    )

    with pytest.raises(HTTPException) as exc:
        await comment_service.update_comment(
            comment_id=str(comment_id),
            student_id=other_id,
            content="Phá hoại",
            ip_address="127.0.0.1",
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["error"]["code"] == "COMMENT_FORBIDDEN"


@pytest.mark.asyncio
async def test_delete_comment_success(mock_db):
    student_id = ObjectId()
    comment_id = ObjectId()
    await mock_db["comments"].insert_one(
        {
            "_id": comment_id,
            "student_id": student_id,
            "content": "Bình luận sắp xóa",
            "status": "visible",
        }
    )

    await comment_service.delete_comment(
        comment_id=str(comment_id), student_id=student_id, ip_address="127.0.0.1"
    )

    db_comment = await mock_db["comments"].find_one({"_id": comment_id})
    assert db_comment["status"] == "deleted"
    assert db_comment["deleted_at"] is not None


@pytest.mark.asyncio
async def test_update_comment_not_found(mock_db):
    student_id = ObjectId()
    with pytest.raises(HTTPException) as exc:
        await comment_service.update_comment(
            comment_id=str(ObjectId()),
            student_id=student_id,
            content="Nội dung mới",
            ip_address="127.0.0.1",
        )
    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "COMMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_comment_not_found(mock_db):
    student_id = ObjectId()
    with pytest.raises(HTTPException) as exc:
        await comment_service.delete_comment(
            comment_id=str(ObjectId()), student_id=student_id, ip_address="127.0.0.1"
        )
    assert exc.value.status_code == 404
    assert exc.value.detail["error"]["code"] == "COMMENT_NOT_FOUND"
