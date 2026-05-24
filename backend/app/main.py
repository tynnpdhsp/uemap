from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.public import (
    health_router,
    config_router,
    categories_router,
    places_router,
    media_router,
)
from app.api.routes.student import (
    auth_router,
    me_router,
    my_places_router,
    uploads_router,
    comments_router,
    reports_router,
)
from app.core.config import settings
from app.core.database import close_db, connect_db
from app.core.minio_client import connect_minio


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    connect_minio()
    yield
    # Shutdown
    await close_db()


# Tạo ứng dụng FastAPI
app = FastAPI(
    title="Bản đồ sinh viên sư phạm API",
    description="API hệ thống bản đồ sinh viên Trường Đại học Sư phạm TP.HCM",
    version="1.0.0",
    openapi_url="/api/openapi.json" if settings.ENV == "dev" else None,
    docs_url="/api/docs" if settings.ENV == "dev" else None,
    redoc_url="/api/redoc" if settings.ENV == "dev" else None,
    lifespan=lifespan,
)

# CORS
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    if isinstance(exc.detail, dict) and ("success" in exc.detail or "error" in exc.detail):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": "HTTP_ERROR", "message": str(exc.detail), "details": []},
        },
    )


# --- Routes ---
# Public
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(config_router, prefix="/api/config", tags=["Map Config"])
app.include_router(categories_router, prefix="/api/categories", tags=["Categories"])
app.include_router(places_router, prefix="/api/places", tags=["Places"])
app.include_router(media_router, prefix="/api/media", tags=["Media"])

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(me_router, prefix="/api/me", tags=["Profile"])
app.include_router(my_places_router, prefix="/api/my/places", tags=["Student Places"])
app.include_router(uploads_router, prefix="/api/uploads", tags=["Student Uploads"])
app.include_router(comments_router, prefix="/api", tags=["Student Comments"])
app.include_router(reports_router, prefix="/api", tags=["Student Reports"])

