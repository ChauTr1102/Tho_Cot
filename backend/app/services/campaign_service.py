"""
Campaign service: orchestrates gen_plan -> gen_assets -> qa_review into the
loop described in draft_idea.txt ("Làm cho đến khi đạt các tiêu chí, và
không có vấn đề phát hiện").

Persists every stage to the JSON file-system store so a human reviewer
can inspect data/<id>/plan.json, assets.json, qa/iteration_N.json.
"""
from __future__ import annotations

from app.schemas.campaign import AssetBundle, CampaignInput, CampaignPlan, QAResult
from app.services.campaign import gen_assets_agent, gen_plan_agent, qa_review_agent
from app.storage.campaign_store import campaign_store


class CampaignService:
    """Business logic layer for running and inspecting campaign pipelines."""

    @staticmethod
    def run_campaign(
        campaign_input: CampaignInput,
        max_iterations: int = qa_review_agent.MAX_ITERATIONS,
    ) -> QAResult:
        campaign_store.save(campaign_input.campaign_id, "input", campaign_input)

        plan: CampaignPlan = gen_plan_agent.generate_plan(campaign_input)
        assets: AssetBundle = gen_assets_agent.generate_assets(plan, campaign_input)

        result: QAResult | None = None
        for iteration in range(1, max_iterations + 1):
            campaign_store.save(campaign_input.campaign_id, "plan", plan)
            campaign_store.save(campaign_input.campaign_id, "assets", assets)

            result = qa_review_agent.review(campaign_input, plan, assets, iteration=iteration)
            campaign_store.save_qa_iteration(campaign_input.campaign_id, iteration, result)

            if result.passed:
                break

            # Regeneration hook: a real gen_plan/gen_assets agent would take
            # `result.issues` as feedback here. Mocks are deterministic, so in
            # this draft we just re-run them once and rely on QA rules to stay
            # satisfied on iteration 2+ once assets pass the checklist.
            plan = gen_plan_agent.generate_plan(campaign_input)
            assets = gen_assets_agent.generate_assets(plan, campaign_input)

        assert result is not None
        return result

    @staticmethod
    def get_latest_qa(campaign_id: str) -> QAResult:
        iterations = campaign_store.list_qa_iterations(campaign_id)
        if not iterations:
            raise FileNotFoundError(f"No QA result found for campaign {campaign_id}.")
        import json

        data = json.loads(iterations[-1].read_text(encoding="utf-8"))
        return QAResult.model_validate(data)


campaign_service = CampaignService()
