from app.api.routes.student.auth import router as auth_router
from app.api.routes.student.comments import router as comments_router
from app.api.routes.student.me import router as me_router
from app.api.routes.student.my_places import router as my_places_router
from app.api.routes.student.reports import router as reports_router
from app.api.routes.student.uploads import router as uploads_router

__all__ = [
    "auth_router",
    "me_router",
    "my_places_router",
    "uploads_router",
    "comments_router",
    "reports_router",
]
