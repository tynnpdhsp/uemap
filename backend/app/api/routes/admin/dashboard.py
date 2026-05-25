from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from app.api.deps import get_current_admin
from app.core.database import get_db

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(current_admin: dict = Depends(get_current_admin)):
    db = get_db()
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    new_reports_count = await db["reports"].count_documents({"status": "new"})
    pending_students_7d_count = await db["students"].count_documents(
        {
            "status": "pending_activation",
            "created_at": {"$gte": seven_days_ago},
        }
    )
    new_published_places_7d_count = await db["places"].count_documents(
        {
            "status": "published",
            "published_at": {"$gte": seven_days_ago},
        }
    )

    return {
        "success": True,
        "data": {
            "new_reports_count": new_reports_count,
            "pending_students_7d_count": pending_students_7d_count,
            "new_published_places_7d_count": new_published_places_7d_count,
            "links": {
                "reports": "/admin/reports?status=new",
                "students": "/admin/students?status=pending_activation",
                "places": "/admin/places?status=published&range=7d",
            },
        },
    }
