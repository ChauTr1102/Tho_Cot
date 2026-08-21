from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    # Initialize database tables
    init_db()
    yield


def create_application() -> FastAPI:
    """FastAPI Application Factory."""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    register_exception_handlers(application)

    # Include Versioned API Routers
    application.include_router(api_router, prefix=settings.API_V1_STR)

    # Serve generated assets. The studio writes images and video under DATA_DIR
    # and hands out /media/... URLs, so the browser can display a kit without
    # the API streaming bytes through itself.
    from pathlib import Path

    from fastapi.staticfiles import StaticFiles

    from app.services.studio.config import studio_settings

    media_root = Path(studio_settings.DATA_DIR)
    media_root.mkdir(parents=True, exist_ok=True)
    application.mount("/media", StaticFiles(directory=media_root), name="media")

    @application.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "docs_url": "/docs",
            "health_check": f"{settings.API_V1_STR}/health",
        }

    return application


app = create_application()
