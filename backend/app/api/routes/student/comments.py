from datetime import timedelta

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import require_active_student
from app.core.database import get_db
from app.schemas.comment import CommentCreateRequest
from app.services import comment_service

router = APIRouter()


@router.post(
    "/places/{public_id}/comments", response_model=dict, status_code=status.HTTP_201_CREATED
)
async def post_student_comment(
    public_id: int,
    payload: CommentCreateRequest,
    request: Request,
    current_student: dict = Depends(require_active_student),
):
    ip = request.client.host if request.client else "127.0.0.1"
    result = await comment_service.create_comment(
        place_public_id=public_id,
        student_id=current_student["_id"],
        student_name=current_student["full_name"],
        content=payload.content,
        ip_address=ip,
    )
    return {"success": True, "data": result}


@router.patch("/comments/{id}", response_model=dict)
async def update_student_comment(
    id: str,
    payload: CommentCreateRequest,
    request: Request,
    current_student: dict = Depends(require_active_student),
):
    ip = request.client.host if request.client else "127.0.0.1"
    await comment_service.update_comment(
        comment_id=id, student_id=current_student["_id"], content=payload.content, ip_address=ip
    )
    return {"success": True, "data": {"message": "Cập nhật bình luận thành công."}}


@router.delete("/comments/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_comment(
    id: str, request: Request, current_student: dict = Depends(require_active_student)
):
    ip = request.client.host if request.client else "127.0.0.1"
    await comment_service.delete_comment(
        comment_id=id, student_id=current_student["_id"], ip_address=ip
    )


@router.get("/my/comments", response_model=dict)
async def get_my_comments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_student: dict = Depends(require_active_student),
):
    db = get_db()
    query = {"student_id": current_student["_id"], "status": "visible"}

    total = await db["comments"].count_documents(query)

    skip = (page - 1) * page_size
    cursor = db["comments"].find(query).sort("created_at", -1).skip(skip).limit(page_size)
    comments = await cursor.to_list(length=page_size)

    place_ids = list(set([c["place_id"] for c in comments]))
    places = await db["places"].find({"_id": {"$in": place_ids}}).to_list(length=100)
    place_map = {p["_id"]: p for p in places}

    formatted = []
    for c in comments:
        p = place_map.get(c["place_id"], {})
        place_name = p.get("name", "Địa điểm cũ")
        place_pub_id = p.get("public_id", 0)

        vn_time = c["created_at"] + timedelta(hours=7)
        created_at_display = vn_time.strftime("%d/%m/%Y %H:%M")

        content_preview = c["content"][:60] + "..." if len(c["content"]) > 60 else c["content"]

        formatted.append(
            {
                "id": str(c["_id"]),
                "content_preview": content_preview,
                "place_name": place_name,
                "place_public_id": place_pub_id,
                "status_label": "hiển thị",
                "created_at_display": created_at_display,
            }
        )

    return {
        "success": True,
        "data": formatted,
        "meta": {"page": page, "page_size": page_size, "total": total},
    }
