"""
Minimal FastAPI app exposing the pipeline for demo/testing.

Endpoints:
  POST /campaigns/run   -> run full pipeline (gen_plan -> gen_assets -> qa_review loop)
  GET  /campaigns/{id}/qa -> latest QA result for a campaign
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.models.schemas import CampaignInput, QAResult
from app.pipeline.orchestrator import run_campaign
from app.storage.store import store

app = FastAPI(title="Commerce Campaign Launch Copilot - BE draft")


@app.post("/campaigns/run", response_model=QAResult)
def run(campaign_input: CampaignInput) -> QAResult:
    return run_campaign(campaign_input)


@app.get("/campaigns/{campaign_id}/qa", response_model=QAResult)
def get_latest_qa(campaign_id: str) -> QAResult:
    iterations = store.list_qa_iterations(campaign_id)
    if not iterations:
        raise HTTPException(status_code=404, detail="No QA result found for this campaign.")
    import json
    data = json.loads(iterations[-1].read_text(encoding="utf-8"))
    return QAResult.model_validate(data)
