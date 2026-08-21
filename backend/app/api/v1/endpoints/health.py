from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.schemas.common import StandardResponse
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=StandardResponse[HealthResponse])
def check_health(db: Session = Depends(get_db)):
    """Check API server and Database health status."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    health_data = HealthResponse(
        status="healthy",
        database=db_status,
        version=settings.VERSION,
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
    )
    return StandardResponse(
        success=True,
        message="Backend is operating normally",
        data=health_data,
    )
