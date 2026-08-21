"""Specialist agents used by ResearchService."""
from dataclasses import dataclass
import logging
import time
import requests
from app.services.research.client import RawModelClient
from app.services.research.prompts import CREATIVE_SYSTEM, EDITOR_SYSTEM, EVIDENCE_AUDITOR_SYSTEM, FOLLOWUP_SEARCH_SYSTEM, OUTPUT_INSTRUCTION, POSITIONING_SYSTEM, RESEARCH_DISCOVERY_SYSTEM, RESEARCH_SYSTEM
from app.services.research.schema import CAMPAIGN_PLAN_SCHEMA, ResearchOutputError

logger = logging.getLogger(__name__)
EXA_MAX_ATTEMPTS = 3
EXA_RETRY_BACKOFF_SECONDS = 0.5


def _exa_with_retry(client: RawModelClient, *, phase: str, on_progress=None, **kwargs):
    """Retry one transient MCP failure without repeating completed phases."""
    last_error: ResearchOutputError | None = None
    for attempt in range(EXA_MAX_ATTEMPTS):
        logger.info("research_agent.exa_attempt phase=%s attempt=%d", phase, attempt + 1)
        try:
            result = client.research_with_exa(on_tool=on_progress, **kwargs)
            logger.info(
                "research_agent.exa_completed phase=%s attempt=%d tool_calls=%d output_chars=%d",
                phase, attempt + 1, len(result[1]), len(result[0]),
            )
            return result
        except (ResearchOutputError, requests.RequestException) as exc:
            last_error = exc if isinstance(exc, ResearchOutputError) else ResearchOutputError(
                f"Lỗi kết nối Exa/ModelArk trong {phase}: {exc}"
            )
            logger.warning(
                "research_agent.exa_failed phase=%s attempt=%d error_type=%s error=%s",
                phase, attempt + 1, type(exc).__name__, exc,
            )
            if attempt < EXA_MAX_ATTEMPTS - 1:
                if on_progress:
                    on_progress(f"thử lại {phase} ({attempt + 2}/{EXA_MAX_ATTEMPTS})")
                time.sleep(EXA_RETRY_BACKOFF_SECONDS * (attempt + 1))
    assert last_error is not None
    raise last_error


def _followup_or_disclose(client: RawModelClient, *, phase: str, on_progress=None, **kwargs):
    """Enrich a downstream draft without making an optional lookup fatal."""
    try:
        return _exa_with_retry(client, phase=phase, on_progress=on_progress, **kwargs)
    except ResearchOutputError as exc:
        logger.warning("research_agent.optional_lookup_skipped phase=%s error=%s", phase, exc)
        if on_progress:
            on_progress(f"bỏ qua {phase}: không có nguồn bổ sung hợp lệ")
        return f"Không có nguồn bổ sung hợp lệ cho {phase}. Không được tạo claim mới. Lỗi: {exc}", []


@dataclass
class ExaResearchAgent:
    client: RawModelClient
    def run(self, brief: str, supplied_evidence: str, *, max_discovery_searches: int = 3,
            images=None, on_progress=None) -> tuple[str, list[str]]:
        discoveries: list[str] = []
        discovery_calls: list[str] = []
        branch_sets = {
            1: {
                "combined": "MARKET + SCIENTIFIC/OFFICIAL + SOCIAL/CONSUMER: tìm ngắn gọn nguồn mạnh nhất cho cả ba nhóm.",
            },
            2: {
                "market/social": "MARKET + SOCIAL/CONSUMER: xu hướng, giá, đối thủ, review, pain point và content format.",
                "scientific/official": "SCIENTIFIC/OFFICIAL: bằng chứng cho thành phần, claim, an toàn và hiệu quả.",
            },
            3: {
                "market": "MARKET: xu hướng, giá, đối thủ, mùa vụ và dữ liệu nền tảng.",
                "scientific/official": "SCIENTIFIC/OFFICIAL: bằng chứng cho thành phần, claim, an toàn và hiệu quả.",
                "social/consumer": "SOCIAL/CONSUMER: review, thảo luận, pain point, ngôn ngữ và content format.",
            },
        }
        branches = branch_sets[max(1, min(3, max_discovery_searches))]
        for phase, assignment in branches.items():
            try:
                discovery, calls = _exa_with_retry(
                    self.client, phase=f"pha tìm kiếm {phase}", on_progress=on_progress,
                    system=RESEARCH_DISCOVERY_SYSTEM,
                    user=(f"NHÁNH ĐƯỢC GIAO: {assignment}\n\nBẢN MÔ TẢ:\n{brief}"
                          f"\n\nBẰNG CHỨNG NGƯỜI DÙNG CUNG CẤP:\n{supplied_evidence}"),
                    required_tool="web_search",
                    images=images,
                )
            except ResearchOutputError as exc:
                logger.error(
                    "research_agent.discovery_branch_degraded phase=%s error=%s", phase, exc
                )
                if on_progress:
                    on_progress(f"bỏ qua nhánh {phase}: Exa không phản hồi sau khi thử lại")
                discovery = (
                    f"Không có kết quả Exa đã xác minh cho nhánh {phase}. "
                    "Không được tạo claim dựa trên nhánh này."
                )
                calls = []
            discoveries.append(f"## {phase.upper()}\n{discovery}")
            discovery_calls.extend(calls)
        discovery_report = "\n\n".join(discoveries)
        try:
            research, verification_calls = _exa_with_retry(
                self.client, phase="pha đọc nguồn", on_progress=on_progress,
                system=RESEARCH_SYSTEM,
                user=(f"BẢN MÔ TẢ:\n{brief}\n\nBẰNG CHỨNG NGƯỜI DÙNG CUNG CẤP:\n{supplied_evidence}"
                      f"\n\nNGUỒN ỨNG VIÊN TỪ BA NHÁNH TÌM KIẾM:\n{discovery_report}"
                      "\n\nBắt buộc mở và đọc các nguồn mạnh nhất cho cả thị trường và người dùng."),
                max_output_tokens=5000,
                required_tool="web_fetch",
                images=images,
            )
        except ResearchOutputError as exc:
            logger.error("research_agent.source_read_degraded error=%s", exc)
            if on_progress:
                on_progress("Exa không đọc được nguồn; tiếp tục ở chế độ an toàn không claim")
            research = (
                "CHẾ ĐỘ AN TOÀN: Exa không trả về nội dung sau khi thử lại pha đọc nguồn. "
                "Các nguồn ứng viên bên dưới chưa được đọc/xác minh; không được dùng chúng để "
                "khẳng định current-market, product, scientific hoặc consumer claim. Chỉ sử dụng "
                "dữ kiện do người dùng cung cấp và ghi rõ giả định.\n\n"
                + discovery_report
            )
            verification_calls = []
        return research, discovery_calls + verification_calls


@dataclass
class PositioningAgent:
    client: RawModelClient
    def run(self, context: str, *, enable_search: bool = True, images=None, on_progress=None) -> tuple[str, list[str]]:
        if not enable_search:
            return self.client.ask(
                system=POSITIONING_SYSTEM,
                user=context + "\nKhông có tìm kiếm bổ sung. Chỉ soạn phần định vị.", images=images,
            ), []
        research, calls = _followup_or_disclose(
            self.client, phase="kiểm tra định vị", on_progress=on_progress,
            system=FOLLOWUP_SEARCH_SYSTEM,
            user=context + "\nTìm đúng khoảng trống quan trọng nhất cho định vị hoặc claim.",
            required_tool="web_search", images=images,
        )
        draft = self.client.ask(
            system=POSITIONING_SYSTEM,
            user=f"{context}\n\nTÌM KIẾM BỔ SUNG:\n{research}\n\nChỉ soạn phần định vị.",
            images=images,
        )
        return draft, calls


@dataclass
class CreativeRoutesAgent:
    client: RawModelClient
    def run(self, context: str, positioning: str, *, enable_search: bool = True,
            images=None, on_progress=None) -> tuple[str, list[str]]:
        if not enable_search:
            return self.client.ask(
                system=CREATIVE_SYSTEM,
                user=f"{context}\n\nĐỊNH VỊ:\n{positioning}\n\nSoạn hai creative routes A/B, mỗi route có mục tiêu và kế hoạch thử nghiệm.",
                images=images,
            ), []
        research, calls = _followup_or_disclose(
            self.client, phase="kiểm tra hướng sáng tạo", on_progress=on_progress,
            system=FOLLOWUP_SEARCH_SYSTEM,
            user=(f"{context}\n\nĐỊNH VỊ:\n{positioning}"
                  "\n\nTìm tín hiệu social/platform tập trung cho hook, ngôn ngữ hoặc format; không xác nhận product claim."),
            required_tool="web_search", images=images,
        )
        draft = self.client.ask(
            system=CREATIVE_SYSTEM,
            user=(f"{context}\n\nĐỊNH VỊ:\n{positioning}\n\nTÌM KIẾM BỔ SUNG:\n{research}"
                  "\n\nSoạn hai creative routes A/B, mỗi route có mục tiêu và kế hoạch thử nghiệm."),
            images=images,
        )
        return draft, calls


@dataclass
class EvidenceAuditorAgent:
    client: RawModelClient
    def run(self, context: str, positioning: str, creative: str, *, enable_search: bool = True,
            images=None, on_progress=None) -> tuple[str, list[str]]:
        if not enable_search:
            return self.client.ask(
                system=EVIDENCE_AUDITOR_SYSTEM,
                user=f"{context}\n\nĐỊNH VỊ:\n{positioning}\n\nSÁNG TẠO:\n{creative}\n\nChỉ trả evidence audit.",
                max_output_tokens=1800, images=images,
            ), []
        research, calls = _followup_or_disclose(
            self.client, phase="kiểm tra bằng chứng", on_progress=on_progress,
            system=FOLLOWUP_SEARCH_SYSTEM,
            user=(f"{context}\n\nĐỊNH VỊ:\n{positioning}\n\nSÁNG TẠO:\n{creative}"
                  "\n\nTìm để kiểm tra claim hoặc nguồn có rủi ro cao nhất; không thêm chiến lược."),
            max_output_tokens=1800, required_tool="web_search", images=images,
        )
        draft = self.client.ask(
            system=EVIDENCE_AUDITOR_SYSTEM,
            user=(f"{context}\n\nĐỊNH VỊ:\n{positioning}\n\nSÁNG TẠO:\n{creative}"
                  f"\n\nTÌM KIẾM KIỂM CHỨNG:\n{research}\n\nChỉ trả evidence audit."),
            max_output_tokens=1800, images=images,
        )
        return draft, calls


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
