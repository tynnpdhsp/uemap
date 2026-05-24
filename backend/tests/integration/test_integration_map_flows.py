from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId

from app.core.database import get_db
from app.core.security import hash_password
from app.services import session_service
from tests.e2e.helpers import (
    api_client,
    assert_error,
    auth_headers,
    clean_auth_db,
    setup_active_student,
)

pytestmark = pytest.mark.integration


async def clean_map_integration_db():
    await clean_auth_db()
    db = get_db()
    await db["categories"].delete_many({})
    await db["places"].delete_many({})
    await db["comments"].delete_many({})
    await db["reports"].delete_many({})
    await db["app_config"].delete_many({"_id": "map"})
    await db["students"].delete_many(
        {"email": {"$in": ["4901104199@student.hcmue.edu.vn", "4901104188@student.hcmue.edu.vn"]}}
    )


@pytest.mark.asyncio
@patch("app.services.upload_service.minio_client", new_callable=AsyncMock)
@patch("app.services.media_service.minio_client", new_callable=AsyncMock)
async def test_map_and_social_integration_flow(mock_media_minio, mock_upload_minio):
    async with api_client() as client:
        await clean_map_integration_db()
        db = get_db()

        cat_res = await db["categories"].insert_one(
            {
                "name": "Ăn uống",
                "color": "#F97316",
                "order": 1,
                "is_hidden": False,
                "created_at": datetime.utcnow(),
            }
        )
        category_id = str(cat_res.inserted_id)

        await db["app_config"].insert_one(
            {
                "_id": "map",
                "geofence": {
                    "type": "rectangle",
                    "bounds": {
                        "sw": {"lat": 10.75, "lng": 106.66},
                        "ne": {"lat": 10.78, "lng": 106.71},
                    },
                },
            }
        )

        token_a = await setup_active_student(client)
        headers_a = auth_headers(token_a)

        student_b_id = ObjectId()
        await db["students"].insert_one(
            {
                "_id": student_b_id,
                "email": "4901104199@student.hcmue.edu.vn",
                "password_hash": hash_password("testpassword123"),
                "full_name": "Nguyễn Văn B",
                "status": "active",
                "created_at": datetime.utcnow(),
            }
        )

        res_login_b = await client.post(
            "/api/auth/login",
            json={"email": "4901104199@student.hcmue.edu.vn", "password": "testpassword123"},
        )
        token_b = res_login_b.json()["data"]["access_token"]
        headers_b = auth_headers(token_b)

        student_locked_id = ObjectId()
        await db["students"].insert_one(
            {
                "_id": student_locked_id,
                "email": "4901104188@student.hcmue.edu.vn",
                "password_hash": hash_password("testpassword123"),
                "full_name": "Locked Student",
                "status": "locked",
                "locked_reason": "Vi phạm chính sách",
                "created_at": datetime.utcnow(),
            }
        )

        token_locked = await session_service.create_session(
            student_locked_id, "127.0.0.1", "pytest"
        )
        headers_locked = auth_headers(token_locked)

        payload_draft = {
            "name": "Quán cơm tấm A",
            "category_id": category_id,
            "scope_type": "near_campus",
            "description": "Quán cơm tấm giá hạt dẻ dành cho sinh viên.",
            "address": "280 An Dương Vương",
            "lat": 10.7628,
            "lng": 106.6824,
            "status": "draft",
            "image_object_keys": [],
            "video": None,
        }
        res = await client.post("/api/my/places", json=payload_draft, headers=headers_a)
        assert res.status_code == 201
        res_data = res.json()["data"]
        assert res_data["status"] == "draft"
        public_id_draft = res_data["public_id"]

        payload_invalid_geo = payload_draft.copy()
        payload_invalid_geo["status"] = "published"
        payload_invalid_geo["lat"] = 11.0
        res = await client.post("/api/my/places", json=payload_invalid_geo, headers=headers_a)
        assert_error(res, 400, "PLACE_OUT_OF_BOUNDS")

        payload_pub = payload_draft.copy()
        payload_pub["status"] = "published"
        res = await client.post("/api/my/places", json=payload_pub, headers=headers_a)
        assert res.status_code == 201
        public_id_pub = res.json()["data"]["public_id"]

        res = await client.get("/api/places/markers")
        assert res.status_code == 200
        markers = res.json()["data"]
        assert len(markers) == 1
        assert markers[0]["public_id"] == public_id_pub

        res = await client.get(f"/api/places/{public_id_pub}")
        assert res.status_code == 200
        assert res.json()["data"]["name"] == "Quán cơm tấm A"

        res = await client.patch(
            f"/api/my/places/{public_id_pub}", json=payload_pub, headers=headers_b
        )
        assert_error(res, 403, "PLACE_FORBIDDEN")

        res = await client.delete(f"/api/my/places/{public_id_pub}", headers=headers_b)
        assert_error(res, 403, "PLACE_FORBIDDEN")

        res = await client.post(
            f"/api/places/{public_id_pub}/comments",
            json={"content": "Đồ ăn rất ngon nha mọi người ơi!"},
            headers=headers_a,
        )
        assert res.status_code == 201
        comment_id = res.json()["data"]["id"]

        res = await client.patch(
            f"/api/comments/{comment_id}", json={"content": "Phá hoại bình luận"}, headers=headers_b
        )
        assert_error(res, 403, "COMMENT_FORBIDDEN")

        res = await client.delete(f"/api/comments/{comment_id}", headers=headers_b)
        assert_error(res, 403, "COMMENT_FORBIDDEN")

        res = await client.post(
            f"/api/places/{public_id_pub}/comments",
            json={"content": "Bình luận trái phép"},
            headers=headers_locked,
        )
        assert_error(res, 403, "AUTH_LOGIN_LOCKED")

        res = await client.post(
            "/api/reports",
            json={
                "target_type": "comment",
                "target_id": comment_id,
                "report_type": "harassment",
                "reason": "Bình luận này có chứa ngôn từ không phù hợp.",
            },
            headers=headers_a,
        )
        assert res.status_code == 201
        assert "report_code" in res.json()["data"]
        assert res.json()["data"]["report_code"].startswith("RP-")

        mock_media_minio.get_object.return_value = [b"image-data"]
        res = await client.get(f"/api/media/places/{public_id_pub}/image1.webp")
        assert res.status_code == 200

        res = await client.get(
            f"/api/media/places/{public_id_draft}/image2.webp", headers=headers_b
        )
        assert res.status_code == 404

        res = await client.delete(f"/api/my/places/{public_id_pub}", headers=headers_a)
        assert res.status_code == 204

        res = await client.get("/api/places/markers")
        assert res.status_code == 200
        assert len(res.json()["data"]) == 0
