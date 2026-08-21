"""
Orchestrator: wires gen_plan -> gen_assets -> qa_review into the loop
described in draft_idea.txt ("Làm cho đến khi đạt các tiêu chí, và
không có vấn đề phát hiện").

Persists every stage to the JSON file-system store so a human reviewer
can inspect campaign/<id>/plan.json, assets.json, qa/iteration_N.json.
"""
from __future__ import annotations

from app.agents import gen_assets_agent, gen_plan_agent, qa_review_agent
from app.models.schemas import AssetBundle, CampaignInput, CampaignPlan, QAResult
from app.storage.store import store


def run_campaign(campaign_input: CampaignInput, max_iterations: int = qa_review_agent.MAX_ITERATIONS) -> QAResult:
    store.save(campaign_input.campaign_id, "input", campaign_input)

    plan: CampaignPlan = gen_plan_agent.generate_plan(campaign_input)
    assets: AssetBundle = gen_assets_agent.generate_assets(plan)

    result: QAResult | None = None
    for iteration in range(1, max_iterations + 1):
        store.save(campaign_input.campaign_id, "plan", plan)
        store.save(campaign_input.campaign_id, "assets", assets)

        result = qa_review_agent.review(campaign_input, plan, assets, iteration=iteration)
        store.save_qa_iteration(campaign_input.campaign_id, iteration, result)

        if result.passed:
            break

        # Regeneration hook: a real gen_plan/gen_assets agent would take
        # `result.issues` as feedback here. Mocks are deterministic, so in
        # this draft we just re-run them once and rely on QA rules to stay
        # satisfied on iteration 2+ once assets pass the checklist.
        plan = gen_plan_agent.generate_plan(campaign_input)
        assets = gen_assets_agent.generate_assets(plan)

    assert result is not None
    return result
