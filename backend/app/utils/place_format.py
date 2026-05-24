from datetime import timedelta

from app.core.database import get_db


def media_url(object_key: str) -> str:
    return f"/api/media/{object_key}"


def format_place_images(images: list[dict]) -> list[dict]:
    formatted = []
    for img in images:
        key = img["object_key"]
        formatted.append(
            {
                "object_key": key,
                "url": media_url(key),
                "sort_order": img.get("sort_order", 0),
                "mime": img["mime"],
            }
        )
    return formatted


def format_place_video(video: dict | None) -> dict | None:
    if not video:
        return None
    data = {
        "kind": video["kind"],
        "object_key": video.get("object_key"),
        "mime": video.get("mime"),
        "url": video.get("url"),
    }
    if video.get("kind") == "file" and video.get("object_key"):
        data["url"] = media_url(video["object_key"])
    return data


async def format_place_list_items(items: list[dict]) -> list[dict]:
    if not items:
        return []

    db = get_db()
    cat_ids = list({p["category_id"] for p in items})
    categories = await db["categories"].find({"_id": {"$in": cat_ids}}).to_list(length=100)
    cat_map = {cat["_id"]: cat["name"] for cat in categories}

    formatted_items = []
    for p in items:
        addr = p.get("address") or ""
        addr_short = addr[:50] + "..." if len(addr) > 50 else addr
        vn_time = p["updated_at"] + timedelta(hours=7)
        updated_at_display = vn_time.strftime("%d/%m/%Y %H:%M")
        formatted_items.append(
            {
                "public_id": p["public_id"],
                "name": p["name"],
                "category_name": cat_map.get(p["category_id"], "Khác"),
                "address_short": addr_short,
                "updated_at_display": updated_at_display,
            }
        )
    return formatted_items
