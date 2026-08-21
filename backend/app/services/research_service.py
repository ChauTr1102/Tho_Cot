"""Authoritative raw-model research and campaign-planning service.

External research uses Exa MCP exclusively; four downstream specialist calls
remain tool-free and produce schema-constrained JSON output.
"""
from __future__ import annotations

import json
import os
import pathlib
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
            model=model, timeout=timeout,
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
        client = self._client(timeout=timeout, model=model)
        if on_progress:
            on_progress("Exa tìm nguồn thị trường và người dùng")
        exa_research, research_tool_calls = ExaResearchAgent(client).run(
            brief_text, evidence_text, images=image_urls,
            on_progress=(lambda name: on_progress(f"Exa gọi {name}")) if on_progress else None,
        )
        context = f"""\
NGÔN NGỮ: Tiếng Việt

{EVIDENCE_POLICY}

PRODUCT BRIEF:
{brief_text}

SUPPLIED EVIDENCE / SOURCES:
{evidence_text}

EXA RESEARCH (NGUỒN BẮT BUỘC CHO CURRENT-MARKET CLAIMS):
{exa_research}
"""
        positioning_agent = PositioningAgent(client)
        creative_agent = CreativeRoutesAgent(client)
        auditor_agent = EvidenceAuditorAgent(client)
        editor_agent = StrategyEditorAgent(client)

        if on_progress:
            on_progress("chuyên gia định vị")
        positioning = positioning_agent.run(context, images=image_urls)
        if on_progress:
            on_progress("chuyên gia hướng sáng tạo")
        creative = creative_agent.run(context, positioning, images=image_urls)
        if on_progress:
            on_progress("chuyên gia kiểm định bằng chứng")
        audit = auditor_agent.run(context, positioning, creative, images=image_urls)
        if on_progress:
            on_progress("biên tập viên chiến lược")
        output = editor_agent.run(context, positioning, creative, audit, images=image_urls)

        try:
            plan = json.loads(output)
            validate_campaign_plan(plan)
        except (json.JSONDecodeError, ResearchOutputError) as exc:
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
        return {
            "engine": "exa_specialists", "status": "completed", "plan": plan,
            "campaign_id": campaign_id,
            "report": json.dumps(plan, ensure_ascii=False, indent=2), "sources": sources,
            "research": exa_research, "research_tool_calls": research_tool_calls,
            "input_assets": asset_manifest,
            "drafts": {"positioning": positioning, "creative": creative, "evidence_audit": audit},
        }


research_service = ResearchService()
