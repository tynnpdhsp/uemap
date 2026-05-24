import os
import sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT, GEOSPHERE

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "ban_do_sv_sp")

def run_migration():
    print(f"Connecting to MongoDB at {MONGODB_URI}...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]

    print("Configuring collection 'categories'...")
    categories_col = db["categories"]
    name_idx = categories_col.create_index([("name", ASCENDING)], unique=True)
    print(f"Created index on categories: {name_idx}")
    
    order_idx = categories_col.create_index([("is_hidden", ASCENDING), ("order", ASCENDING)])
    print(f"Created index on categories: {order_idx}")

    print("Configuring place counters...")
    db["place_counters"].update_one(
        {"_id": "places"},
        {"$setOnInsert": {"seq": 0}},
        upsert=True
    )

    print("Configuring collection 'places'...")
    places_col = db["places"]
    
    pub_id_idx = places_col.create_index([("public_id", ASCENDING)], unique=True)
    print(f"Created index on places: {pub_id_idx}")
    
    status_cat_idx = places_col.create_index([("status", ASCENDING), ("category_id", ASCENDING)])
    print(f"Created index on places: {status_cat_idx}")
    
    creator_idx = places_col.create_index([
        ("creator_student_id", ASCENDING),
        ("status", ASCENDING),
        ("updated_at", DESCENDING)
    ])
    print(f"Created index on places: {creator_idx}")
    
    loc_idx = places_col.create_index([("location", GEOSPHERE)])
    print(f"Created 2dsphere index on places: {loc_idx}")
    
    text_idx = places_col.create_index([
        ("name", TEXT),
        ("description", TEXT)
    ], weights={"name": 10, "description": 2})
    print(f"Created text index on places: {text_idx}")

    print("Configuring collection 'comments'...")
    comments_col = db["comments"]
    
    place_comm_idx = comments_col.create_index([
        ("place_id", ASCENDING),
        ("status", ASCENDING),
        ("created_at", DESCENDING)
    ])
    print(f"Created index on comments: {place_comm_idx}")
    
    student_comm_idx = comments_col.create_index([
        ("student_id", ASCENDING),
        ("created_at", DESCENDING)
    ])
    print(f"Created index on comments: {student_comm_idx}")

    print("Configuring collection 'reports'...")
    reports_col = db["reports"]
    
    rep_code_idx = reports_col.create_index([("report_code", ASCENDING)], unique=True)
    print(f"Created index on reports: {rep_code_idx}")
    
    rep_student_idx = reports_col.create_index([
        ("reporter_student_id", ASCENDING),
        ("created_at", DESCENDING)
    ])
    print(f"Created index on reports: {rep_student_idx}")
    
    rep_status_idx = reports_col.create_index([
        ("status", ASCENDING),
        ("created_at", DESCENDING)
    ])
    print(f"Created index on reports: {rep_status_idx}")

    print("Configuring collection 'app_config'...")
    app_config_col = db["app_config"]
    app_config_col.update_one(
        {"_id": "map"},
        {"$setOnInsert": {
            "default_center": {"lat": 10.7628, "lng": 106.6824},
            "default_zoom": 16,
            "geofence": {
                "type": "rectangle",
                "bounds": {
                    "sw": {"lat": 10.75, "lng": 106.66},
                    "ne": {"lat": 10.78, "lng": 106.71}
                }
            },
            "cluster_zoom_threshold": 14,
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )
    print("App config seeded.")

    print("Migration 002_map_places_and_social.py completed successfully!")
    client.close()

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Error running migration: {e}", file=sys.stderr)
        sys.exit(1)
