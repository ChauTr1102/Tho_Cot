from fastapi import APIRouter

from app.api.v1.endpoints import health, items, research, studio

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(research.router, prefix="/research", tags=["Research"])
api_router.include_router(studio.router, prefix="/studio", tags=["Asset Studio"])
