from typing import List, Optional

from fastapi import APIRouter, Query

from app.services import search_service
from app.utils.place_format import format_place_list_items

router = APIRouter()


@router.get("", response_model=dict)
async def search_places(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_ids: Optional[List[str]] = Query(None),
):
    result = await search_service.search_places(
        q=q,
        category_ids=category_ids,
        page=page,
        page_size=page_size,
    )
    formatted_items = await format_place_list_items(result["items"])
    return {
        "success": True,
        "data": formatted_items,
        "meta": {
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"],
        },
    }
