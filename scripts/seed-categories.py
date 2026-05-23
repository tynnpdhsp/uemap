#!/usr/bin/env python
# Script seed 4 danh mục mặc định vào MongoDB

import os
import sys
from pymongo import MongoClient


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ban_do_sv_sp")


def seed_categories():
    print(f"Connecting to MongoDB at {MONGODB_URI}...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    categories_col = db["categories"]

    default_categories = [
        {
            "name": "hành chính của trường",
            "color": "#1E40AF",  # Xanh dương đậm
            "order": 1,
            "description": "Các đơn vị, phòng ban, trung tâm hành chính thuộc trường",
            "is_hidden": False,
        },
        {
            "name": "quán ăn và uống",
            "color": "#F97316",  # Cam
            "order": 2,
            "description": "Quán ăn, nhà hàng, quán cà phê gần hoặc trong trường",
            "is_hidden": False,
        },
        {
            "name": "quán in ấn",
            "color": "#8B5CF6",  # Tím
            "order": 3,
            "description": "Cửa hàng photocopy, in ấn, văn phòng phẩm",
            "is_hidden": False,
        },
        {
            "name": "tiện ích gần trường",
            "color": "#10B981",  # Xanh lá
            "order": 4,
            "description": "Các tiện ích khác như nhà thuốc, siêu thị tiện lợi, trạm xe buýt",
            "is_hidden": False,
        },
    ]

    inserted_count = 0
    updated_count = 0

    for cat in default_categories:
        existing = categories_col.find_one({"name": cat["name"]})
        if not existing:
            categories_col.insert_one(cat)
            print(f"Inserted default category: '{cat['name']}'")
            inserted_count += 1
        else:
            categories_col.update_one({"_id": existing["_id"]}, {"$set": cat})
            print(f"Updated existing category: '{cat['name']}'")
            updated_count += 1

    print(f"Seeding completed. Inserted: {inserted_count}, Updated: {updated_count}")
    client.close()


if __name__ == "__main__":
    try:
        seed_categories()
    except Exception as e:
        print(f"Error seeding categories: {e}", file=sys.stderr)
        sys.exit(1)
