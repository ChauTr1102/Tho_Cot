"""Specialist agents used by ResearchService."""
from dataclasses import dataclass
from app.services.research.client import RawModelClient
from app.services.research.prompts import CREATIVE_SYSTEM, EDITOR_SYSTEM, EVIDENCE_AUDITOR_SYSTEM, OUTPUT_INSTRUCTION, POSITIONING_SYSTEM, RESEARCH_DISCOVERY_SYSTEM, RESEARCH_SYSTEM
from app.services.research.schema import CAMPAIGN_PLAN_SCHEMA, ResearchOutputError


def _exa_with_retry(client: RawModelClient, *, phase: str, on_progress=None, **kwargs):
    """Retry one transient MCP failure without repeating completed phases."""
    last_error: ResearchOutputError | None = None
    for attempt in range(2):
        try:
            return client.research_with_exa(on_tool=on_progress, **kwargs)
        except ResearchOutputError as exc:
            last_error = exc
            if attempt == 0 and on_progress:
                on_progress(f"thử lại {phase}")
    assert last_error is not None
    raise last_error


@dataclass
class ExaResearchAgent:
    client: RawModelClient
    def run(self, brief: str, supplied_evidence: str, *, images=None, on_progress=None) -> tuple[str, list[str]]:
        discovery, discovery_calls = _exa_with_retry(
            self.client, phase="pha tìm kiếm", on_progress=on_progress,
            system=RESEARCH_DISCOVERY_SYSTEM,
            user=f"BẢN MÔ TẢ:\n{brief}\n\nBẰNG CHỨNG NGƯỜI DÙNG CUNG CẤP:\n{supplied_evidence}",
            required_tool="web_search",
            images=images,
        )
        research, verification_calls = _exa_with_retry(
            self.client, phase="pha đọc nguồn", on_progress=on_progress,
            system=RESEARCH_SYSTEM,
            user=(f"BẢN MÔ TẢ:\n{brief}\n\nBẰNG CHỨNG NGƯỜI DÙNG CUNG CẤP:\n{supplied_evidence}"
                  f"\n\nNGUỒN ỨNG VIÊN TỪ PHA TÌM KIẾM:\n{discovery}"
                  "\n\nBắt buộc mở và đọc các nguồn mạnh nhất cho cả thị trường và người dùng."),
            max_output_tokens=5000,
            required_tool="web_fetch",
            images=images,
        )
        return research, discovery_calls + verification_calls


@dataclass
class PositioningAgent:
    client: RawModelClient
    def run(self, context: str, *, images=None) -> str:
        return self.client.ask(system=POSITIONING_SYSTEM, user=context + "\nChỉ soạn phần định vị.", images=images)


@dataclass
class CreativeRoutesAgent:
    client: RawModelClient
    def run(self, context: str, positioning: str, *, images=None) -> str:
        return self.client.ask(system=CREATIVE_SYSTEM, user=f"{context}\n\nĐỊNH VỊ:\n{positioning}\n\nSoạn hai creative routes A/B.", images=images)


@dataclass
class EvidenceAuditorAgent:
    client: RawModelClient
    def run(self, context: str, positioning: str, creative: str, *, images=None) -> str:
        return self.client.ask(system=EVIDENCE_AUDITOR_SYSTEM,
                               user=f"{context}\n\nĐỊNH VỊ:\n{positioning}\n\nSÁNG TẠO:\n{creative}\n\nChỉ trả evidence audit.",
                               max_output_tokens=1400, images=images)


@dataclass
class StrategyEditorAgent:
    client: RawModelClient
    def run(self, context: str, positioning: str, creative: str, audit: str, *, images=None) -> str:
        return self.client.ask(
            system=EDITOR_SYSTEM,
            user=f"{context}\n\nPOSITIONING:\n{positioning}\n\nCREATIVE:\n{creative}\n\nAUDIT BẮT BUỘC:\n{audit}\n\n{OUTPUT_INSTRUCTION}",
            # Kế hoạch có evidence theo từng quyết định thường vượt 5k token.
            # Chừa đủ chỗ để JSON đóng hoàn chỉnh thay vì bị cắt giữa chuỗi.
            max_output_tokens=9000, json_schema=CAMPAIGN_PLAN_SCHEMA, images=images,
        )

    def repair(self, context: str, invalid_output: str, error: str, *, images=None) -> str:
        return self.client.ask(
            system=EDITOR_SYSTEM,
            user=(f"{context}\n\nJSON TRƯỚC ĐÓ KHÔNG HỢP LỆ:\n{invalid_output}"
                  f"\n\nLỖI KIỂM TRA:\n{error}"
                  f"\n\nHãy sửa đúng lỗi, giữ nguyên dữ kiện có căn cứ.\n{OUTPUT_INSTRUCTION}"),
            max_output_tokens=9000,
            json_schema=CAMPAIGN_PLAN_SCHEMA,
            images=images,
        )
