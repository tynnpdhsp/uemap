from fastapi import APIRouter
from app.core.database import get_db

router = APIRouter()

@router.get("", response_model=dict)
async def get_categories():
    db = get_db()
    cursor = db["categories"].find({"is_hidden": False}).sort("order", 1)
    categories = await cursor.to_list(length=100)
    
    formatted = []
    for cat in categories:
        formatted.append({
            "id": str(cat["_id"]),
            "name": cat["name"],
            "color": cat["color"],
            "order": cat.get("order", 0),
            "icon_url": cat.get("icon_url"),
            "description": cat.get("description")
        })

    return {"success": True, "data": formatted}
