from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException, status
from bson import ObjectId
from app.core.database import get_db
from app.services import search_service

router = APIRouter()

@router.get("/markers", response_model=dict)
async def get_markers(
    category_ids: Optional[List[str]] = Query(None),
    sw_lat: Optional[float] = Query(None),
    sw_lng: Optional[float] = Query(None),
    ne_lat: Optional[float] = Query(None),
    ne_lng: Optional[float] = Query(None)
):
    db = get_db()
    query = {"status": "published"}

    if category_ids:
        oids = []
        for cid in category_ids:
            try:
                oids.append(ObjectId(cid))
            except Exception:
                pass
        if oids:
            query["category_id"] = {"$in": oids}

    if sw_lat is not None and sw_lng is not None and ne_lat is not None and ne_lng is not None:
        query["location"] = {
            "$geoWithin": {
                "$box": [[sw_lng, sw_lat], [ne_lng, ne_lat]]
            }
        }

    cursor = db["places"].find(query)
    places = await cursor.to_list(length=1000)

    cat_ids = list(set([p["category_id"] for p in places]))
    categories = await db["categories"].find({"_id": {"$in": cat_ids}}).to_list(length=100)
    cat_map = {cat["_id"]: cat for cat in categories}

    formatted = []
    for p in places:
        cat = cat_map.get(p["category_id"], {})
        coords = p["location"]["coordinates"]
        addr = p["address"]
        addr_short = addr[:50] + "..." if len(addr) > 50 else addr
        
        formatted.append({
            "public_id": p["public_id"],
            "name": p["name"],
            "lat": coords[1],
            "lng": coords[0],
            "category_id": str(p["category_id"]),
            "category_color": cat.get("color", "#3B82F6"),
            "category_icon_url": cat.get("icon_url"),
            "address_short": addr_short
        })

    return {"success": True, "data": formatted}

@router.get("", response_model=dict)
async def get_places(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_ids: Optional[List[str]] = Query(None),
    q: Optional[str] = Query(None),
    sort: str = Query("updated_desc")
):
    if q and len(q.strip()) >= 2:
        result = await search_service.search_places(
            q=q,
            category_ids=category_ids,
            page=page,
            page_size=page_size
        )
    else:
        db = get_db()
        query = {"status": "published"}

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

        sort_query = [("updated_at", -1)]
        if sort == "name_asc":
            sort_query = [("name", 1)]
        elif sort == "updated_desc":
            sort_query = [("updated_at", -1)]

        skip = (page - 1) * page_size
        cursor = db["places"].find(query).sort(sort_query).skip(skip).limit(page_size)
        items = await cursor.to_list(length=page_size)
        
        result = {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    db = get_db()
    cat_ids = list(set([p["category_id"] for p in result["items"]]))
    categories = await db["categories"].find({"_id": {"$in": cat_ids}}).to_list(length=100)
    cat_map = {cat["_id"]: cat["name"] for cat in categories}

    formatted_items = []
    for p in result["items"]:
        addr = p["address"]
        addr_short = addr[:50] + "..." if len(addr) > 50 else addr
        
        vn_time = p["updated_at"] + timedelta(hours=7)
        updated_at_display = vn_time.strftime("%d/%m/%Y %H:%M")
        
        formatted_items.append({
            "public_id": p["public_id"],
            "name": p["name"],
            "category_name": cat_map.get(p["category_id"], "Khác"),
            "address_short": addr_short,
            "updated_at_display": updated_at_display
        })

    return {
        "success": True,
        "data": formatted_items,
        "meta": {
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"]
        }
    }

@router.get("/{public_id}", response_model=dict)
async def get_place_detail(public_id: int):
    db = get_db()
    place = await db["places"].find_one({"public_id": public_id, "status": "published"})
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_NOT_FOUND",
                    "message": "Không tìm thấy địa điểm hoặc địa điểm chưa được công khai.",
                    "details": []
                }
            }
        )

    student = await db["students"].find_one({"_id": place["creator_student_id"]})
    creator_name = student["full_name"] if student else "Sinh viên"

    category = await db["categories"].find_one({"_id": place["category_id"]})
    category_name = category["name"] if category else "Khác"

    scope_label_map = {
        "on_campus": "Trong trường",
        "near_campus": "Gần trường"
    }

    vn_time = place["updated_at"] + timedelta(hours=7)
    updated_at_display = vn_time.strftime("%d/%m/%Y %H:%M")

    formatted_images = []
    for img in place.get("images", []):
        formatted_images.append({
            "object_key": img["object_key"],
            "sort_order": img.get("sort_order", 0),
            "mime": img["mime"]
        })

    video_data = None
    if place.get("video"):
        v = place["video"]
        video_data = {
            "kind": v["kind"],
            "object_key": v.get("object_key"),
            "mime": v.get("mime"),
            "url": v.get("url")
        }

    data = {
        "public_id": place["public_id"],
        "creator_student_id": str(place["creator_student_id"]),
        "creator_student_name": creator_name,
        "category_id": str(place["category_id"]),
        "category_name": category_name,
        "scope_type": place["scope_type"],
        "scope_label": scope_label_map.get(place["scope_type"], place["scope_type"]),
        "name": place["name"],
        "description": place["description"],
        "address": place["address"],
        "location": {
            "type": "Point",
            "coordinates": place["location"]["coordinates"]
        },
        "hours": place.get("hours"),
        "contact": place.get("contact"),
        "images": formatted_images,
        "video": video_data,
        "updated_at_display": updated_at_display
    }

    return {"success": True, "data": data}

@router.get("/{public_id}/comments", response_model=dict)
async def get_place_comments(
    public_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    db = get_db()
    place = await db["places"].find_one({"public_id": public_id, "status": "published"})
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": {
                    "code": "PLACE_NOT_FOUND",
                    "message": "Không tìm thấy địa điểm hoặc địa điểm chưa được công khai.",
                    "details": []
                }
            }
        )

    query = {"place_id": place["_id"], "status": "visible"}
    total = await db["comments"].count_documents(query)

    skip = (page - 1) * page_size
    cursor = db["comments"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    comments = await cursor.to_list(length=page_size)

    formatted = []
    for c in comments:
        vn_time = c["created_at"] + timedelta(hours=7)
        created_at_display = vn_time.strftime("%d/%m/%Y %H:%M")
        
        formatted.append({
            "id": str(c["_id"]),
            "author_display_name": c["author_display_name"],
            "content": c["content"],
            "created_at_display": created_at_display
        })

    return {
        "success": True,
        "data": formatted,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total
        }
    }
