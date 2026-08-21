"""Authoritative raw-model research and campaign-planning service.

External research uses Exa MCP exclusively; four downstream specialist calls
remain tool-free and produce schema-constrained JSON output.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
import time
from collections.abc import Callable

from app.services.research import (
    CreativeRoutesAgent, DEFAULT_BASE_URL, DEFAULT_MODEL, EvidenceAuditorAgent, ExaResearchAgent,
    PositioningAgent, RawModelClient, ResearchOutputError, StrategyEditorAgent,
    validate_campaign_plan,
)
from app.services.research.input import load_visual_assets, validate_research_input
from app.services.research.prompts import EVIDENCE_POLICY

_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[2]
_WORKSPACE_ROOT = _BACKEND_DIR.parent
EXA_DISCOVERY_SEARCHES = 1
EXA_FOLLOWUP_SEARCHES = 0
logger = logging.getLogger(__name__)


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


class ResearchService:
    def __init__(self, client: RawModelClient | None = None) -> None:
        self.client = client

    def _client(self, *, timeout: float, model: str) -> RawModelClient:
        if self.client is not None:
            return self.client
        api_key = _env("ARK_API_KEY")
        if not api_key:
            raise RuntimeError("Thiếu ARK_API_KEY trong environment hoặc backend/.env")
        return RawModelClient(
            api_key, base_url=_env("ARK_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL,
            model=model, timeout=timeout, exa_api_key=_env("EXA_API_KEY"),
        )

    def run(
        self,
        brief: str | None = None,
        *,
        research_input: dict | None = None,
        visual_assets: tuple[list[str], list[dict]] | None = None,
        evidence: str | None = None,
        lang: str = "vi",
        timeout: float = 420,
        model: str = DEFAULT_MODEL,
        workspace_root: pathlib.Path | None = None,
        on_progress: Callable[[str], None] | None = None,
        **_: object,
    ) -> dict:
        started_at = time.monotonic()
        if research_input is not None and brief and brief.strip():
            raise ValueError("Chỉ truyền brief hoặc research_input, không truyền đồng thời")
        image_urls: list[str] = []
        asset_manifest: list[dict] = []
        campaign_id: str | None = None
        if research_input is not None:
            structured = validate_research_input(research_input)
            if visual_assets is not None:
                image_urls, asset_manifest = visual_assets
            else:
                image_urls, asset_manifest = load_visual_assets(
                    structured, workspace_root or _WORKSPACE_ROOT,
                )
            campaign_id = structured["campaign_id"]
            brief_text = (
                "RESEARCH INPUT CÓ CẤU TRÚC (giữ nguyên null và mảng rỗng; không tự điền):\n"
                + json.dumps(structured, ensure_ascii=False, indent=2)
                + "\n\nDANH SÁCH ẢNH ĐÃ KIỂM TRA VÀ GỬI KÈM:\n"
                + json.dumps(asset_manifest, ensure_ascii=False, indent=2)
            )
        elif brief and brief.strip():
            brief_text = brief.strip()
        else:
            raise ValueError("brief hoặc research_input không được để trống")
        if lang != "vi":
            raise ValueError("Đầu ra chỉ hỗ trợ tiếng Việt")
        evidence_text = evidence.strip() if evidence and evidence.strip() else "Không có tệp evidence từ người dùng."
        logger.info(
            "research_service.started campaign_id=%s input_type=%s assets=%d evidence_supplied=%s model=%s",
            campaign_id,
            "structured" if research_input is not None else "brief",
            len(image_urls),
            bool(evidence and evidence.strip()),
            model,
        )
        client = self._client(timeout=timeout, model=model)
        if on_progress:
            on_progress("Exa tìm nguồn thị trường và người dùng")
        exa_research, research_tool_calls = ExaResearchAgent(client).run(
            brief_text, evidence_text, images=image_urls,
            max_discovery_searches=EXA_DISCOVERY_SEARCHES,
            on_progress=(lambda name: on_progress(f"Exa gọi {name}")) if on_progress else None,
        )
        logger.info(
            "research_service.stage_completed campaign_id=%s stage=exa_research duration_ms=%d "
            "tool_calls=%d output_chars=%d",
            campaign_id,
            round((time.monotonic() - started_at) * 1000),
            len(research_tool_calls),
            len(exa_research),
        )
        context = f"""\
NGÔN NGỮ: Tiếng Việt

{EVIDENCE_POLICY}

PRODUCT BRIEF:
{brief_text}

SUPPLIED EVIDENCE / SOURCES:
{evidence_text}

USER ACTUALLY SUPPLIED EXTERNAL EVIDENCE: {bool(evidence and evidence.strip())}

EXA RESEARCH (NGUỒN BẮT BUỘC CHO CURRENT-MARKET CLAIMS):
{exa_research}
"""
        positioning_agent = PositioningAgent(client)
        creative_agent = CreativeRoutesAgent(client)
        auditor_agent = EvidenceAuditorAgent(client)
        editor_agent = StrategyEditorAgent(client)

        if on_progress:
            on_progress("chuyên gia định vị")
        positioning, positioning_calls = positioning_agent.run(
            context, images=image_urls,
            enable_search=EXA_FOLLOWUP_SEARCHES >= 2,
            on_progress=(lambda name: on_progress(f"định vị gọi {name}")) if on_progress else None,
        )
        logger.info(
            "research_service.stage_completed campaign_id=%s stage=positioning tool_calls=%d output_chars=%d",
            campaign_id, len(positioning_calls), len(positioning),
        )
        if on_progress:
            on_progress("chuyên gia hướng sáng tạo")
        creative, creative_calls = creative_agent.run(
            context, positioning, images=image_urls,
            enable_search=EXA_FOLLOWUP_SEARCHES >= 3,
            on_progress=(lambda name: on_progress(f"sáng tạo gọi {name}")) if on_progress else None,
        )
        logger.info(
            "research_service.stage_completed campaign_id=%s stage=creative tool_calls=%d output_chars=%d",
            campaign_id, len(creative_calls), len(creative),
        )
        if on_progress:
            on_progress("chuyên gia kiểm định bằng chứng")
        audit, audit_calls = auditor_agent.run(
            context, positioning, creative, images=image_urls,
            enable_search=EXA_FOLLOWUP_SEARCHES >= 1,
            on_progress=(lambda name: on_progress(f"kiểm định gọi {name}")) if on_progress else None,
        )
        logger.info(
            "research_service.stage_completed campaign_id=%s stage=evidence_audit tool_calls=%d output_chars=%d",
            campaign_id, len(audit_calls), len(audit),
        )
        if on_progress:
            on_progress("biên tập viên chiến lược")
        output = editor_agent.run(context, positioning, creative, audit, images=image_urls)
        logger.info(
            "research_service.stage_completed campaign_id=%s stage=strategy_editor output_chars=%d",
            campaign_id, len(output),
        )

        try:
            plan = json.loads(output)
            validate_campaign_plan(plan)
        except (json.JSONDecodeError, ResearchOutputError) as exc:
            logger.warning(
                "research_service.plan_repair_started campaign_id=%s error_type=%s error=%s",
                campaign_id, type(exc).__name__, exc,
            )
            if on_progress:
                on_progress("biên tập viên sửa JSON chưa đạt schema")
            output = editor_agent.repair(context, output, str(exc), images=image_urls)
            try:
                plan = json.loads(output)
            except json.JSONDecodeError as repair_exc:
                raise ResearchOutputError(
                    f"Kết quả sửa vẫn không phải JSON hợp lệ: {repair_exc}"
                ) from repair_exc
            validate_campaign_plan(plan)
        sources = [
            source["url"] for source in plan["source_summary"]["sources"]
            if source.get("url")
        ]
        result = {
            "engine": "exa_specialists", "status": "completed", "plan": plan,
            "campaign_id": campaign_id,
            "report": json.dumps(plan, ensure_ascii=False, indent=2), "sources": sources,
            "research": exa_research,
            "research_tool_calls": research_tool_calls + positioning_calls + creative_calls + audit_calls,
            "input_assets": asset_manifest,
            "drafts": {"positioning": positioning, "creative": creative, "evidence_audit": audit},
        }
        logger.info(
            "research_service.completed campaign_id=%s duration_ms=%d sources=%d total_tool_calls=%d",
            campaign_id,
            round((time.monotonic() - started_at) * 1000),
            len(sources),
            len(result["research_tool_calls"]),
        )
        return result


research_service = ResearchService()
