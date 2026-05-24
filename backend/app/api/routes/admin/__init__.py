from app.api.routes.admin.admins import router as admin_admins_router
from app.api.routes.admin.audit_logs import router as admin_audit_logs_router
from app.api.routes.admin.auth import router as admin_auth_router
from app.api.routes.admin.categories import router as admin_categories_router
from app.api.routes.admin.comments import router as admin_comments_router
from app.api.routes.admin.config import router as admin_config_router
from app.api.routes.admin.dashboard import router as admin_dashboard_router
from app.api.routes.admin.places import router as admin_places_router
from app.api.routes.admin.reports import router as admin_reports_router
from app.api.routes.admin.students import router as admin_students_router

__all__ = [
    "admin_auth_router",
    "admin_dashboard_router",
    "admin_categories_router",
    "admin_places_router",
    "admin_comments_router",
    "admin_reports_router",
    "admin_students_router",
    "admin_admins_router",
    "admin_audit_logs_router",
    "admin_config_router",
]
