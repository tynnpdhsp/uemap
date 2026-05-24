import pytest
from bson import ObjectId

from app.services import search_service

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_search_places_by_query(mock_db):
    cat_id = ObjectId()
    await mock_db["places"].insert_one(
        {
            "name": "Bánh mì Sư Phạm",
            "description": "Bánh mì thịt siêu ngon dành cho sinh viên.",
            "status": "published",
            "category_id": cat_id,
        }
    )
    await mock_db["places"].insert_one(
        {
            "name": "Cà phê võng",
            "description": "Nơi nghỉ ngơi trưa thoáng mát sạch sẽ.",
            "status": "published",
            "category_id": cat_id,
        }
    )
    await mock_db["places"].insert_one(
        {
            "name": "Quán nháp chưa công bố",
            "description": "Quán này ở trạng thái draft nên không tìm thấy.",
            "status": "draft",
            "category_id": cat_id,
        }
    )

    res1 = await search_service.search_places("Sư Phạm")
    assert res1["total"] == 1
    assert res1["items"][0]["name"] == "Bánh mì Sư Phạm"

    res2 = await search_service.search_places("nghỉ ngơi")
    assert res2["total"] == 1
    assert res2["items"][0]["name"] == "Cà phê võng"

    res3 = await search_service.search_places("bún bò")
    assert res3["total"] == 0


@pytest.mark.asyncio
async def test_search_places_filter_category(mock_db):
    cat_food = ObjectId()
    cat_drink = ObjectId()

    await mock_db["places"].insert_one(
        {
            "name": "Quán cơm tấm",
            "description": "Ăn trưa no bụng nhiều sườn.",
            "status": "published",
            "category_id": cat_food,
        }
    )
    await mock_db["places"].insert_one(
        {
            "name": "Trà sữa nhà làm",
            "description": "Ngon ngọt ngào mát lạnh ngày hè.",
            "status": "published",
            "category_id": cat_drink,
        }
    )

    res = await search_service.search_places(q="", category_ids=[str(cat_food)])
    assert res["total"] == 1
    assert res["items"][0]["name"] == "Quán cơm tấm"
