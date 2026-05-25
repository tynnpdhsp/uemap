from bson import ObjectId


async def seed_map_test_config(mock_db) -> None:
    await mock_db["app_config"].insert_one(
        {
            "_id": "map",
            "default_center": {"lat": 10.7628, "lng": 106.6824},
            "geofence": {
                "type": "rectangle",
                "bounds": {
                    "sw": {"lat": 10.75, "lng": 106.66},
                    "ne": {"lat": 10.78, "lng": 106.71},
                },
            },
        }
    )


async def seed_visible_category(mock_db, name: str = "Quán ăn") -> ObjectId:
    cat_id = ObjectId()
    await mock_db["categories"].insert_one(
        {"_id": cat_id, "name": name, "is_hidden": False, "order": 1, "color": "#000"}
    )
    return cat_id
