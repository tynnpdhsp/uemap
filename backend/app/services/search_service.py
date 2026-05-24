from typing import List, Optional
from bson import ObjectId
from app.core.database import get_db

async def search_places(
    q: str,
    category_ids: Optional[List[str]] = None,
    page: int = 1,
    page_size: int = 20
) -> dict:
    db = get_db()
    
    query = {"status": "published"}

    if q and q.strip():
        search_term = q.strip()
        query["$or"] = [
            {"name": {"$regex": search_term, "$options": "i"}},
            {"description": {"$regex": search_term, "$options": "i"}}
        ]

    if category_ids:
        oids = []
        for cid in category_ids:
            try:
                oids.append(ObjectId(cid))
            except Exception:
                pass
        if oids:
            query["category_id"] = {"$in": oids}

    total = await db["places"].count_documents(query)

    skip = (page - 1) * page_size
    cursor = db["places"].find(query).skip(skip).limit(page_size)
    places = await cursor.to_list(length=page_size)

    return {
        "items": places,
        "total": total,
        "page": page,
        "page_size": page_size
    }
