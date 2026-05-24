from app.api.routes.student.auth import router as auth_router
from app.api.routes.student.me import router as me_router

__all__ = ["auth_router", "me_router"]
