from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.campaign import Campaign
from app.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignService:
    @staticmethod
    def list(db: Session, *, skip: int = 0, limit: int = 50) -> list[Campaign]:
        return (
            db.query(Campaign)
            .order_by(Campaign.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get(db: Session, campaign_id: str) -> Campaign:
        campaign = db.get(Campaign, campaign_id)
        if campaign is None:
            raise NotFoundException(f"Campaign with ID {campaign_id} does not exist")
        return campaign

    @staticmethod
    def create(db: Session, payload: CampaignCreate) -> Campaign:
        if db.get(Campaign, payload.id) is not None:
            raise BadRequestException(f"Campaign with ID {payload.id} already exists")
        campaign = Campaign(**payload.model_dump())
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def update(db: Session, campaign_id: str, payload: CampaignUpdate) -> Campaign:
        campaign = CampaignService.get(db, campaign_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(campaign, field, value)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def delete(db: Session, campaign_id: str) -> Campaign:
        campaign = CampaignService.get(db, campaign_id)
        db.delete(campaign)
        db.commit()
        return campaign

    @staticmethod
    def start_research(db: Session, *, campaign_id: str, research_input: dict) -> Campaign:
        campaign = db.get(Campaign, campaign_id)
        if campaign is None:
            product_name = research_input.get("product_brief", {}).get("product_name")
            campaign = Campaign(id=campaign_id, name=product_name or campaign_id)
            db.add(campaign)
        campaign.research_input = research_input
        campaign.status = "researching"
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def save_research_result(db: Session, *, campaign_id: str, result: dict) -> Campaign:
        campaign = CampaignService.get(db, campaign_id)
        campaign.research_result = result
        campaign.status = "researched"
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def mark_research_failed(db: Session, *, campaign_id: str) -> None:
        campaign = db.get(Campaign, campaign_id)
        if campaign is not None:
            campaign.status = "failed"
            db.commit()


campaign_service = CampaignService()

