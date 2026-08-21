from fastapi import APIRouter

from app.api.v1.endpoints import (
    campaigns,
    extractor,
    health,
    items,
    research,
    studio,
    verify_checklist,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(research.router, prefix="/research", tags=["Research"])
api_router.include_router(extractor.router, prefix="/extractor", tags=["Extractor"])
api_router.include_router(
    verify_checklist.router, prefix="/verify-checklist", tags=["Verify Checklist"]
)
api_router.include_router(studio.router, prefix="/studio", tags=["Asset Studio"])
