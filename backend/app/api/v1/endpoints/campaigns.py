from fastapi import APIRouter, status

from app.core.exceptions import NotFoundException
from app.schemas.campaign import CampaignInput, QAResult
from app.schemas.common import StandardResponse
from app.services.campaign_service import campaign_service

router = APIRouter()


@router.post("/run", response_model=StandardResponse[QAResult], status_code=status.HTTP_201_CREATED)
def run_campaign(payload: CampaignInput):
    """Run the full campaign pipeline (gen_plan -> gen_assets -> qa_review loop)."""
    result = campaign_service.run_campaign(payload)
    return StandardResponse(
        success=True,
        message="Campaign pipeline completed" if result.passed else "Campaign pipeline finished with unresolved QA issues",
        data=result,
    )


@router.get("/{campaign_id}/qa", response_model=StandardResponse[QAResult])
def get_latest_qa(campaign_id: str):
    """Retrieve the latest QA review result for a campaign."""
    try:
        result = campaign_service.get_latest_qa(campaign_id)
    except FileNotFoundError:
        raise NotFoundException(message=f"No QA result found for campaign '{campaign_id}'.")
    return StandardResponse(
        success=True,
        message="Latest QA result retrieved",
        data=result,
    )
