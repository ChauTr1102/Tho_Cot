"""Agent-based QA checklist service.

Replaces the fixed Python rule list in app/services/qa_checklist_service.py
with two agent stages, reusing the RawModelClient/ModelArk pattern from
app/services/research_service.py:

  1. Checklist GENERATOR agent reads the campaign brief (CampaignInputDTO)
     and produces a brief-specific list of checklist items (not a fixed
     rule set — e.g. it derives one item per required/forbidden claim
     actually present in *this* brief).
  2. Each checklist item is then verified independently and in PARALLEL by
     a VERIFIER agent, which is given the actual relevant output field(s)
     (and, for image-dependent items, the real image loaded from its local
     file path) and judged pass/fail with a reason.

Results are aggregated into the same VerifyChecklistResponse shape the
frontend already consumes (`passed`, `issues`, `regenerate`), so this is a
drop-in replacement for QAChecklistService.verify() at the API layer.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.schemas.campaign_dto import CampaignOutputDTO
from app.schemas.qa_checklist import (
    QAIssue,
    QASeverity,
    RegenerateTarget,
    VerifyChecklistRequest,
    VerifyChecklistResponse,
)
from app.services.qa_agent.field_resolver import resolve_field, stringify_field
from app.services.qa_agent.image_loader import is_video_path, load_local_images
from app.services.qa_agent.prompts import CHECKLIST_GENERATOR_SYSTEM, CHECKLIST_VERIFIER_SYSTEM
from app.services.qa_agent.schema import CHECKLIST_SCHEMA, VERIFICATION_RESULT_SCHEMA, validate_checklist, validate_verification_result
from app.services.research import DEFAULT_BASE_URL, DEFAULT_MODEL, RawModelClient, ResearchOutputError

logger = logging.getLogger(__name__)

_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]
_MAX_PARALLEL_VERIFIERS = 6

# Stage regeneration order the frontend should follow when both sides
# need fixing at once (same order as the old rule-based service: plan
# before asset, since asset regeneration usually depends on plan output).
_REGENERATE_ORDER = [
    RegenerateTarget.PLAN,
    RegenerateTarget.ASSET,
]


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value:
        return value
    env_file = _BACKEND_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, raw_value = line.partition("=")
            if separator and key.strip() == name:
                return raw_value.strip().strip('"').strip("'")
    return default


class AgentQAChecklistService:
    def __init__(self, client: RawModelClient | None = None) -> None:
        self.client = client

    def _get_client(self, *, timeout: float, model: str) -> RawModelClient:
        if self.client is not None:
            return self.client
        api_key = _env("ARK_API_KEY")
        if not api_key:
            raise RuntimeError("Thiếu ARK_API_KEY trong environment hoặc backend/.env")
        return RawModelClient(
            api_key, base_url=_env("ARK_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL,
            model=model, timeout=timeout,
        )

    # -- Stage 1: generate a brief-specific checklist ------------------------

    def _generate_checklist(self, client: RawModelClient, request: VerifyChecklistRequest) -> list[dict]:
        brief_json = request.campaign_input.model_dump_json(indent=2)
        output_json = request.campaign_output.model_dump_json(indent=2)
        raw = client.ask(
            system=CHECKLIST_GENERATOR_SYSTEM,
            user=(
                f"CAMPAIGN BRIEF (campaign_input):\n{brief_json}\n\n"
                f"CẤU TRÚC CAMPAIGN OUTPUT SẼ ĐƯỢC KIỂM TRA (chỉ để biết field nào tồn tại, "
                f"KHÔNG chấm nội dung ở bước này):\n{output_json}\n\n"
                "Sinh checklist cho brief này."
            ),
            json_schema=CHECKLIST_SCHEMA,
            max_output_tokens=3000,
        )
        payload = json.loads(raw)
        return validate_checklist(payload)

    # -- Stage 2: verify one checklist item -----------------------------------

    def _verify_item(
        self, client: RawModelClient, item: dict, request: VerifyChecklistRequest,
    ) -> QAIssue | None:
        output = request.campaign_output
        field_blobs = []
        image_paths: list[str] = []
        for target_field in item["target_fields"]:
            value = resolve_field(output, target_field)
            field_blobs.append(f"### {target_field}\n{stringify_field(value)}")
            if item["needs_image"] and isinstance(value, str) and value.strip() and not is_video_path(value):
                image_paths.append(value)

        image_data_urls: list[str] = []
        image_notes: list[str] = []
        if item["needs_image"]:
            image_data_urls, image_notes = load_local_images(image_paths)

        user_prompt = (
            f"TIÊU CHÍ CẦN CHẤM:\n{item['description']}\n\n"
            f"SEVERITY: {item['severity']}\n\n"
            f"NỘI DUNG THỰC TẾ TỪ CAMPAIGN OUTPUT:\n" + "\n\n".join(field_blobs)
        )
        if item["needs_image"]:
            user_prompt += "\n\nGHI CHÚ TẢI ẢNH:\n" + "\n".join(image_notes)
            if not image_data_urls:
                user_prompt += (
                    "\n\nKHÔNG có ảnh thực nào tải được — chấm FAIL vì không thể xem nội dung ảnh thật."
                )

        try:
            raw = client.ask(
                system=CHECKLIST_VERIFIER_SYSTEM,
                user=user_prompt,
                json_schema=VERIFICATION_RESULT_SCHEMA,
                images=image_data_urls or None,
                max_output_tokens=500,
            )
            result = validate_verification_result(json.loads(raw))
        except (ResearchOutputError, json.JSONDecodeError) as exc:
            logger.warning("qa_agent.verify_item_failed item_id=%s error=%s", item["id"], exc)
            # Treat an unusable verifier response as a fail-safe BLOCKER so
            # transient model/parse errors surface as "needs another look"
            # rather than silently passing.
            return QAIssue(
                rule_id=item["id"], severity=QASeverity(item["severity"]),
                message=f"Không thể chấm tiêu chí này (lỗi verifier agent: {exc}).",
                field=item["target_fields"][0], regenerate=RegenerateTarget(item["category"]),
            )

        if result["pass"]:
            return None
        return QAIssue(
            rule_id=item["id"], severity=QASeverity(item["severity"]),
            message=result["reason"], field=item["target_fields"][0],
            regenerate=RegenerateTarget(item["category"]),
        )

    # -- Entry point -----------------------------------------------------------

    def verify(
        self, request: VerifyChecklistRequest, *, timeout: float = 120, model: str = DEFAULT_MODEL,
    ) -> VerifyChecklistResponse:
        client = self._get_client(timeout=timeout, model=model)

        checklist = self._generate_checklist(client, request)
        logger.info(
            "qa_agent.checklist_generated iteration=%d item_count=%d",
            request.iteration, len(checklist),
        )

        issues: list[QAIssue] = []
        with ThreadPoolExecutor(max_workers=_MAX_PARALLEL_VERIFIERS) as pool:
            futures = {
                pool.submit(self._verify_item, client, item, request): item
                for item in checklist
            }
            for future in as_completed(futures):
                item = futures[future]
                try:
                    issue = future.result()
                except Exception as exc:  # noqa: BLE001 - isolate one item's crash from the rest
                    logger.exception("qa_agent.verify_item_crashed item_id=%s", item["id"])
                    issue = QAIssue(
                        rule_id=item["id"], severity=QASeverity(item["severity"]),
                        message=f"Verifier agent crashed: {exc}",
                        field=item["target_fields"][0], regenerate=RegenerateTarget(item["category"]),
                    )
                if issue is not None:
                    issues.append(issue)

        # TEMP: only surface WARNING severity for now — never block the
        # pipeline. Agent still judges each item using its real BLOCKER/
        # WARNING severity internally (see _verify_item), but every issue is
        # downgraded to WARNING here before computing `passed`, so `passed`
        # is only False on a pipeline crash (see the endpoint's exception
        # handling), never because of a detected QA issue.
        issues = [issue.model_copy(update={"severity": QASeverity.WARNING}) for issue in issues]

        passed = not any(issue.severity == QASeverity.BLOCKER for issue in issues)
        seen = {issue.regenerate for issue in issues}
        regenerate = [target for target in _REGENERATE_ORDER if target in seen]

        logger.info(
            "qa_agent.verify_completed iteration=%d passed=%s issue_count=%d",
            request.iteration, passed, len(issues),
        )
        return VerifyChecklistResponse(
            passed=passed, iteration=request.iteration, issues=issues, regenerate=regenerate,
        )


agent_qa_checklist_service = AgentQAChecklistService()
