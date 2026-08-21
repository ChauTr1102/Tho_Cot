from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_pagination
from app.schemas.campaign import CampaignCreate, CampaignListItem, CampaignOut, CampaignUpdate
from app.schemas.common import PaginationParams, StandardResponse
from app.services.campaign_service import campaign_service

router = APIRouter()


@router.get("", response_model=StandardResponse[list[CampaignListItem]])
def list_campaigns(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
):
    campaigns = campaign_service.list(db, skip=pagination.skip, limit=pagination.limit)
    data = [
        CampaignListItem(
            id=item.id,
            name=item.name,
            description=item.description,
            status=item.status,
            has_research_result=item.research_result is not None,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in campaigns
    ]
    return StandardResponse(message=f"Retrieved {len(data)} campaigns", data=data)


@router.get("/{campaign_id}", response_model=StandardResponse[CampaignOut])
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    return StandardResponse(data=campaign_service.get(db, campaign_id))


@router.post("", response_model=StandardResponse[CampaignOut], status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    return StandardResponse(message="Campaign created successfully", data=campaign_service.create(db, payload))


@router.patch("/{campaign_id}", response_model=StandardResponse[CampaignOut])
def update_campaign(campaign_id: str, payload: CampaignUpdate, db: Session = Depends(get_db)):
    return StandardResponse(
        message="Campaign updated successfully",
        data=campaign_service.update(db, campaign_id, payload),
    )


@router.delete("/{campaign_id}", response_model=StandardResponse[dict])
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    campaign_service.delete(db, campaign_id)
    return StandardResponse(message="Campaign deleted successfully", data={"id": campaign_id})

