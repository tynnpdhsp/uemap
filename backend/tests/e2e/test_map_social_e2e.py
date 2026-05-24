from datetime import datetime
from unittest.mock import AsyncMock, patch
import pytest
from bson import ObjectId
from app.core.database import get_db
from app.core.security import hash_password
from app.services import session_service
from tests.e2e.helpers import (
    api_client,
    clean_auth_db,
    setup_active_student,
    auth_headers,
    assert_error
)

pytestmark = pytest.mark.e2e

async def clean_map_e2e_db():
    await clean_auth_db()
    db = get_db()
    await db["categories"].delete_many({})
    await db["places"].delete_many({})
    await db["comments"].delete_many({})
    await db["reports"].delete_many({})
    await db["app_config"].delete_many({"_id": "map"})
    await db["students"].delete_many({"email": "4901104199@student.hcmue.edu.vn"})

@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_e2e_map_place_creation_and_bounds(mock_media_minio, mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()

        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)

        await db["app_config"].insert_one({
            "_id": "map",
            "geofence": {
                "type": "rectangle",
                "bounds": {
                    "sw": {"lat": 10.75, "lng": 106.66},
                    "ne": {"lat": 10.78, "lng": 106.71}
                }
            }
        })

        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        payload = {
            "name": "Quán cơm tấm E2E",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán cơm tấm ngon bổ rẻ dành cho sinh viên.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "draft",
            "image_object_keys": [],
            "video": None
        }

        res = await client.post("/api/my/places", json=payload, headers=headers_a)
        assert res.status_code == 201
        public_id = res.json()["data"]["public_id"]

        payload_invalid = payload.copy()
        payload_invalid["status"] = "published"
        payload_invalid["lat"] = 11.0
        res = await client.patch(f"/api/my/places/{public_id}", json=payload_invalid, headers=headers_a)
        assert_error(res, 400, "PLACE_OUT_OF_BOUNDS")

        payload_valid = payload.copy()
        payload_valid["status"] = "published"
        res = await client.patch(f"/api/my/places/{public_id}", json=payload_valid, headers=headers_a)
        assert res.status_code == 200

        res = await client.get("/api/places/markers")
        assert res.status_code == 200
        markers = res.json()["data"]
        assert len(markers) == 1
        assert markers[0]["public_id"] == public_id

@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_e2e_map_social_interactions(mock_media_minio, mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()

        cat_res = await db["categories"].insert_one({
            "name": "Giải trí",
            "color": "#3B82F6",
            "order": 2,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)

        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        student_b_id = ObjectId()
        await db["students"].insert_one({
            "_id": student_b_id,
            "email": "4901104199@student.hcmue.edu.vn",
            "password_hash": hash_password("testpassword123"),
            "full_name": "Nguyễn Văn B",
            "status": "active",
            "created_at": datetime.utcnow()
        })

        res_login_b = await client.post(
            "/api/auth/login",
            json={"email": "4901104199@student.hcmue.edu.vn", "password": "testpassword123"}
        )
        token_b = res_login_b.json()["data"]["access_token"]
        headers_b = auth_headers(token_b)

        payload = {
            "name": "Sân bóng đá mini",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Sân cỏ nhân tạo thoáng mát sạch đẹp thể thao.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "published",
            "image_object_keys": [],
            "video": None
        }

        res = await client.post("/api/my/places", json=payload, headers=headers_a)
        assert res.status_code == 201
        public_id = res.json()["data"]["public_id"]

        res = await client.post(
            f"/api/places/{public_id}/comments",
            json={"content": "Sân bóng đá rất chất lượng nha mọi người!"},
            headers=headers_b
        )
        assert res.status_code == 201
        comment_id = res.json()["data"]["id"]

        res = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Đồng ý, sân bóng đá rất chất lượng nha mọi người!"},
            headers=headers_a
        )
        assert_error(res, 403, "COMMENT_FORBIDDEN")

        res = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Cập nhật bình luận thành công bởi sinh viên B"},
            headers=headers_b
        )
        assert res.status_code == 200

        res = await client.post(
            "/api/reports",
            json={
                "target_type": "comment",
                "target_id": comment_id,
                "report_type": "inappropriate_content",
                "reason": "Báo cáo nội dung bình luận không phù hợp trên trang."
            },
            headers=headers_a
        )
        assert res.status_code == 201
        assert "report_code" in res.json()["data"]


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
async def test_e2e_map_geofence_types(mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()

        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)

        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        payload = {
            "name": "Quán cơm tấm E2E",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán cơm tấm ngon bổ rẻ dành cho sinh viên.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "published",
            "image_object_keys": [],
            "video": None
        }

        res = await client.post("/api/my/places", json=payload, headers=headers_a)
        assert res.status_code == 201

        await db["app_config"].insert_one({
            "_id": "map",
            "geofence": {
                "type": "radius",
                "center": {"lat": 10.7628, "lng": 106.6824},
                "radius_meters": 1000.0
            }
        })

        payload["lat"] = 10.7630
        payload["lng"] = 106.6820
        res = await client.post("/api/my/places", json=payload, headers=headers_a)
        assert res.status_code == 201

        payload["lat"] = 10.9000
        res = await client.post("/api/my/places", json=payload, headers=headers_a)
        assert_error(res, 400, "PLACE_OUT_OF_BOUNDS")


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
async def test_e2e_map_places_list_and_search(mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()

        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)

        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        payload_1 = {
            "name": "Quán bún bò Huế ngon",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán bún bò Huế cực ngon sườn chả bò gân đầy đủ.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "published",
            "image_object_keys": [],
            "video": None
        }
        await client.post("/api/my/places", json=payload_1, headers=headers_a)

        payload_2 = {
            "name": "Cà phê Sân Vườn",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Không gian thoáng mát yên tĩnh thích hợp học tập.",
            "address": "282 An Dương Vương",
            "lat": 10.7625,
            "lng": 106.6820,
            "status": "published",
            "image_object_keys": [],
            "video": None
        }
        await client.post("/api/my/places", json=payload_2, headers=headers_a)

        res = await client.get("/api/places?q=bún bò")
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) == 1
        assert data[0]["name"] == "Quán bún bò Huế ngon"

        res = await client.get(f"/api/places?category_id={category_id}")
        assert res.status_code == 200
        assert len(res.json()["data"]) == 2


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
async def test_e2e_comment_soft_delete_and_list(mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()

        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)

        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        payload = {
            "name": "Quán cơm tấm E2E",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán cơm tấm ngon bổ rẻ dành cho sinh viên.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "published",
            "image_object_keys": [],
            "video": None
        }

        res = await client.post("/api/my/places", json=payload, headers=headers_a)
        assert res.status_code == 201
        public_id = res.json()["data"]["public_id"]

        res = await client.post(
            f"/api/places/{public_id}/comments",
            json={"content": "Bình luận số một cực hay nha mọi người!"},
            headers=headers_a
        )
        assert res.status_code == 201
        comment_id = res.json()["data"]["id"]

        res = await client.get(f"/api/places/{public_id}/comments")
        assert res.status_code == 200
        assert len(res.json()["data"]) == 1

        res = await client.delete(f"/api/comments/{comment_id}", headers=headers_a)
        assert res.status_code == 204

        res = await client.get(f"/api/places/{public_id}/comments")
        assert res.status_code == 200
        assert len(res.json()["data"]) == 0


@pytest.mark.asyncio
async def test_e2e_map_config_and_categories():
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()
        await db["app_config"].insert_one({
            "_id": "map",
            "geofence": {
                "type": "radius",
                "center": {"lat": 10.76, "lng": 106.68},
                "radius_meters": 500.0
            }
        })
        await db["categories"].insert_many([
            {"name": "Cat B", "color": "#111111", "order": 2, "is_hidden": False, "created_at": datetime.utcnow()},
            {"name": "Cat A", "color": "#222222", "order": 1, "is_hidden": False, "created_at": datetime.utcnow()},
            {"name": "Cat C", "color": "#333333", "order": 3, "is_hidden": True, "created_at": datetime.utcnow()}
        ])
        res = await client.get("/api/config/map")
        assert res.status_code == 200
        assert res.json()["data"]["geofence"]["type"] == "radius"
        res = await client.get("/api/categories")
        assert res.status_code == 200
        cats = res.json()["data"]
        assert len(cats) == 2
        assert cats[0]["name"] == "Cat A"
        assert cats[1]["name"] == "Cat B"


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
async def test_e2e_place_validation_and_failures(mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()
        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)
        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        student_b_id = ObjectId()
        await db["students"].insert_one({
            "_id": student_b_id,
            "email": "4901104199@student.hcmue.edu.vn",
            "password_hash": hash_password("testpassword123"),
            "full_name": "Nguyễn Văn B",
            "status": "active",
            "created_at": datetime.utcnow()
        })
        res_login_b = await client.post(
            "/api/auth/login",
            json={"email": "4901104199@student.hcmue.edu.vn", "password": "testpassword123"}
        )
        token_b = res_login_b.json()["data"]["access_token"]
        headers_b = auth_headers(token_b)

        payload_short_name = {
            "name": "Cơm",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán cơm tấm ngon bổ rẻ dành cho sinh viên.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "draft",
            "image_object_keys": [],
            "video": None
        }
        res = await client.post("/api/my/places", json=payload_short_name, headers=headers_a)
        assert res.status_code == 422

        payload_valid = payload_short_name.copy()
        payload_valid["name"] = "Quán cơm tấm ngon tuyệt vời"
        res = await client.post("/api/my/places", json=payload_valid, headers=headers_a)
        assert res.status_code == 201
        public_id = res.json()["data"]["public_id"]

        res = await client.get(f"/api/places/{public_id}")
        assert res.status_code == 404

        res = await client.get(f"/api/my/places/{public_id}", headers=headers_a)
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "Quán cơm tấm ngon tuyệt vời"

        res = await client.get(f"/api/my/places/{public_id}", headers=headers_b)
        assert_error(res, 403, "PLACE_FORBIDDEN")

        payload_update = payload_valid.copy()
        payload_update["name"] = "Cập nhật bởi sinh viên khác"
        res = await client.patch(f"/api/my/places/{public_id}", json=payload_update, headers=headers_b)
        assert_error(res, 403, "PLACE_FORBIDDEN")

        res = await client.delete(f"/api/my/places/{public_id}", headers=headers_b)
        assert_error(res, 403, "PLACE_FORBIDDEN")

        res = await client.delete(f"/api/my/places/{public_id}", headers=headers_a)
        assert res.status_code == 204

        res = await client.get(f"/api/my/places/{public_id}", headers=headers_a)
        assert_error(res, 404, "PLACE_NOT_FOUND")


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
async def test_e2e_comments_validation_and_failures(mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()
        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)
        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        student_b_id = ObjectId()
        await db["students"].insert_one({
            "_id": student_b_id,
            "email": "4901104199@student.hcmue.edu.vn",
            "password_hash": hash_password("testpassword123"),
            "full_name": "Nguyễn Văn B",
            "status": "active",
            "created_at": datetime.utcnow()
        })
        res_login_b = await client.post(
            "/api/auth/login",
            json={"email": "4901104199@student.hcmue.edu.vn", "password": "testpassword123"}
        )
        token_b = res_login_b.json()["data"]["access_token"]
        headers_b = auth_headers(token_b)

        payload_draft = {
            "name": "Quán cơm tấm ngon tuyệt vời",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán cơm tấm ngon bổ rẻ dành cho sinh viên.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "draft",
            "image_object_keys": [],
            "video": None
        }
        res = await client.post("/api/my/places", json=payload_draft, headers=headers_a)
        public_id = res.json()["data"]["public_id"]

        res = await client.post(
            f"/api/places/{public_id}/comments",
            json={"content": "Bình luận thử trên bản nháp"},
            headers=headers_b
        )
        assert_error(res, 403, "COMMENT_FORBIDDEN")

        res = await client.post(
            "/api/places/99999/comments",
            json={"content": "Bình luận thử trên địa điểm không tồn tại"},
            headers=headers_b
        )
        assert_error(res, 403, "COMMENT_FORBIDDEN")

        payload_pub = payload_draft.copy()
        payload_pub["status"] = "published"
        res = await client.patch(f"/api/my/places/{public_id}", json=payload_pub, headers=headers_a)
        assert res.status_code == 200

        res = await client.post(
            f"/api/places/{public_id}/comments",
            json={"content": "Bình luận hợp lệ trên bản published"},
            headers=headers_b
        )
        assert res.status_code == 201
        comment_id = res.json()["data"]["id"]

        res = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Cố gắng sửa bình luận của người khác"},
            headers=headers_a
        )
        assert_error(res, 403, "COMMENT_FORBIDDEN")

        res = await client.delete(
            f"/api/comments/{comment_id}",
            headers=headers_a
        )
        assert_error(res, 403, "COMMENT_FORBIDDEN")

        res = await client.get("/api/my/comments", headers=headers_b)
        assert res.status_code == 200
        comments_b = res.json()["data"]
        assert len(comments_b) == 1
        assert comments_b[0]["id"] == comment_id


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
async def test_e2e_reports_validation_and_failures(mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()
        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)
        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        payload = {
            "name": "Quán cơm tấm ngon tuyệt vời",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán cơm tấm ngon bổ rẻ dành cho sinh viên.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "published",
            "image_object_keys": [],
            "video": None
        }
        res = await client.post("/api/my/places", json=payload, headers=headers_a)
        public_id = res.json()["data"]["public_id"]

        res = await client.post(
            "/api/reports",
            json={
                "target_type": "place",
                "target_id": "99999",
                "report_type": "wrong_info",
                "reason": "Địa điểm không chính xác và cần được cập nhật sớm nhất"
            },
            headers=headers_a
        )
        assert_error(res, 404, "PLACE_NOT_FOUND")

        res = await client.post(
            "/api/reports",
            json={
                "target_type": "comment",
                "target_id": str(ObjectId()),
                "report_type": "inappropriate_content",
                "reason": "Báo cáo nội dung bình luận thô tục phản cảm"
            },
            headers=headers_a
        )
        assert_error(res, 404, "COMMENT_NOT_FOUND")

        res = await client.post(
            "/api/reports",
            json={
                "target_type": "invalid_type",
                "target_id": "123",
                "report_type": "wrong_info",
                "reason": "Nội dung báo cáo lỗi lý do chi tiết dài hơn hai mươi kí tự"
            },
            headers=headers_a
        )
        assert_error(res, 400, "REPORT_FORBIDDEN")

        res = await client.post(
            "/api/reports",
            json={
                "target_type": "place",
                "target_id": str(public_id),
                "report_type": "wrong_info",
                "reason": "Địa điểm này có thông tin sai lệch"
            },
            headers=headers_a
        )
        assert res.status_code == 201

        res = await client.get("/api/my/reports", headers=headers_a)
        assert res.status_code == 200
        reports_list = res.json()["data"]
        assert len(reports_list) == 1
        assert reports_list[0]["target_type"] == "place"


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
async def test_e2e_uploads_validation_and_failures(mock_upload_minio):
    async with api_client() as client:
        await clean_map_e2e_db()
        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        files = [("files", ("test.png", b"image-data", "image/png"))]
        res = await client.post("/api/uploads/images", files=files, headers=headers_a)
        assert res.status_code == 201
        assert "object_keys" in res.json()

        files_large = [("files", (f"img_{i}.png", b"img-data", "image/png")) for i in range(11)]
        res = await client.post("/api/uploads/images", files=files_large, headers=headers_a)
        assert_error(res, 400, "VALIDATION_ERROR")

        files_invalid_mime = [("files", ("test.pdf", b"pdf-data", "application/pdf"))]
        res = await client.post("/api/uploads/images", files=files_invalid_mime, headers=headers_a)
        assert_error(res, 400, "FILE_TYPE_INVALID")

        large_bytes = b"x" * (5 * 1024 * 1024 + 1)
        files_large_size = [("files", ("large.png", large_bytes, "image/png"))]
        res = await client.post("/api/uploads/images", files=files_large_size, headers=headers_a)
        assert_error(res, 400, "FILE_SIZE_EXCEEDED")

        res = await client.post(
            "/api/uploads/video",
            files={"file": ("video.avi", b"video-data", "video/avi")},
            headers=headers_a
        )
        assert_error(res, 400, "FILE_TYPE_INVALID")

        large_vid_bytes = b"x" * (80 * 1024 * 1024 + 1)
        res = await client.post(
            "/api/uploads/video",
            files={"file": ("large_video.mp4", large_vid_bytes, "video/mp4")},
            headers=headers_a
        )
        assert_error(res, 400, "FILE_SIZE_EXCEEDED")

        res = await client.post(
            "/api/uploads/video",
            files={"file": ("video.mp4", b"video-data", "video/mp4")},
            headers=headers_a
        )
        assert res.status_code == 201
        assert "object_key" in res.json()


@pytest.mark.asyncio
@patch("app.services.media_service.minio_client")
async def test_e2e_media_permissions(mock_media_minio):
    mock_media_minio.get_object = AsyncMock(return_value=[b"fake-media-data"])
    async with api_client() as client:
        await clean_map_e2e_db()
        db = get_db()
        cat_res = await db["categories"].insert_one({
            "name": "Ăn uống",
            "color": "#F97316",
            "order": 1,
            "is_hidden": False,
            "created_at": datetime.utcnow()
        })
        category_id = str(cat_res.inserted_id)

        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        student_b_id = ObjectId()
        await db["students"].insert_one({
            "_id": student_b_id,
            "email": "4901104199@student.hcmue.edu.vn",
            "password_hash": hash_password("testpassword123"),
            "full_name": "Nguyễn Văn B",
            "status": "active",
            "created_at": datetime.utcnow()
        })
        res_login_b = await client.post(
            "/api/auth/login",
            json={"email": "4901104199@student.hcmue.edu.vn", "password": "testpassword123"}
        )
        token_b = res_login_b.json()["data"]["access_token"]
        headers_b = auth_headers(token_b)

        await db["places"].insert_many([
            {
                "public_id": 1,
                "creator_student_id": ObjectId(student_b_id),
                "category_id": ObjectId(category_id),
                "scope_type": "near_campus",
                "name": "Quán cơm sinh viên B (Draft)",
                "description": "Quán cơm bình dân giá rẻ cho sinh viên",
                "address": "280 An Dương Vương",
                "location": {"type": "Point", "coordinates": [106.6824, 10.7628]},
                "hours": None,
                "contact": None,
                "status": "draft",
                "images": [{"object_key": "places/1/image1.jpg", "sort_order": 0, "mime": "image/jpeg"}],
                "video": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "public_id": 2,
                "creator_student_id": ObjectId(student_b_id),
                "category_id": ObjectId(category_id),
                "scope_type": "near_campus",
                "name": "Quán lẩu sinh viên B (Published)",
                "description": "Quán lẩu ngon rẻ cho sinh viên tụ tập",
                "address": "280 An Dương Vương",
                "location": {"type": "Point", "coordinates": [106.6824, 10.7628]},
                "hours": None,
                "contact": None,
                "status": "published",
                "images": [{"object_key": "places/2/image1.jpg", "sort_order": 0, "mime": "image/jpeg"}],
                "video": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ])

        res = await client.get("/api/media/places/1/image1.jpg", headers=headers_a)
        assert res.status_code == 404

        res = await client.get("/api/media/places/1/image1.jpg", headers=headers_b)
        assert res.status_code == 200
        assert res.read() == b"fake-media-data"

        res = await client.get("/api/media/places/2/image1.jpg", headers=headers_a)
        assert res.status_code == 200
        assert res.read() == b"fake-media-data"

        res = await client.get(f"/api/media/uploads/{str(student_b_id)}/test.png", headers=headers_a)
        assert res.status_code == 404

        res = await client.get(f"/api/media/uploads/{str(student_b_id)}/test.png", headers=headers_b)
        assert res.status_code == 200
        assert res.read() == b"fake-media-data"
