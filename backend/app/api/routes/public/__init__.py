from app.api.routes.public.categories import router as categories_router
from app.api.routes.public.config import router as config_router
from app.api.routes.public.health import router as health_router
from app.api.routes.public.media import router as media_router
from app.api.routes.public.places import router as places_router
from app.api.routes.public.search import router as search_router

__all__ = [
    "health_router",
    "config_router",
    "categories_router",
    "places_router",
    "search_router",
    "media_router",
]
