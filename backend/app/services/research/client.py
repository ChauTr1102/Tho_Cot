"""ModelArk client: raw specialist calls plus one Exa-only research call."""
import json
import re
from collections.abc import Callable
from typing import Any
import requests
from app.services.research.schema import ResearchOutputError

DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
DEFAULT_MODEL = "dola-seed-2-1-turbo-260628"
EXA_MCP_URL = "https://mcp.exa.ai/mcp"


def extract_output_text(response: dict[str, Any]) -> str:
    direct = response.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    parts = []
    for item in response.get("output", []):
        if isinstance(item, dict) and item.get("type") == "message":
            parts.extend(
                block.get("text", "") for block in item.get("content", [])
                if isinstance(block, dict) and block.get("type") == "output_text"
            )
    text = "".join(parts).strip()
    if not text:
        raise ResearchOutputError("Phản hồi ModelArk không chứa output_text")
    return text


class RawModelClient:
    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL,
                 model: str = DEFAULT_MODEL, timeout: float = 420,
                 post: Callable[..., Any] | None = None) -> None:
        if not api_key:
            raise ValueError("Bắt buộc phải có ARK_API_KEY")
        self.api_key, self.base_url, self.model, self.timeout = api_key, base_url.rstrip("/"), model, timeout
        self.post = post or requests.post

    @staticmethod
    def _user_content(user: str, images: list[str] | None = None) -> str | list[dict[str, str]]:
        if not images:
            return user
        return ([{"type": "input_text", "text": user}] + [
            {"type": "input_image", "image_url": image_url} for image_url in images
        ])

    def ask(self, *, system: str, user: str, max_output_tokens: int = 2200,
            json_schema: dict[str, Any] | None = None,
            images: list[str] | None = None) -> str:
        body: dict[str, Any] = {
            "model": self.model, "stream": False, "thinking": {"type": "disabled"},
            "max_output_tokens": max_output_tokens,
            "input": [{"role": "system", "content": system}, {
                "role": "user", "content": self._user_content(user, images),
            }],
        }
        if json_schema is not None:
            body["text"] = {"format": {
                "type": "json_schema", "name": "campaign_plan",
                "schema": json_schema, "strict": True,
            }}
        response = self.post(
            f"{self.base_url}/responses",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=body, timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise ResearchOutputError(
                f"ModelArk /responses failed ({response.status_code}): {response.text[:1000]}"
            ) from exc
        return extract_output_text(response.json())

    def research_with_exa(self, *, system: str, user: str,
                          max_output_tokens: int = 3000,
                          required_tool: str | None = None,
                          images: list[str] | None = None,
                          on_tool: Callable[[str], None] | None = None) -> tuple[str, list[str]]:
        """Run the only tool-enabled stage, using Exa MCP exclusively."""
        response = self.post(
            f"{self.base_url}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "ark-beta-mcp": "true",
            },
            json={
                "model": self.model,
                "stream": True,
                "max_output_tokens": max_output_tokens,
                "tools": [{
                    "type": "mcp", "server_label": "exa", "server_url": EXA_MCP_URL,
                    "require_approval": "never",
                }],
                "input": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": self._user_content(user, images)},
                ],
            },
            timeout=self.timeout,
            stream=True,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise ResearchOutputError(
                f"ModelArk Exa MCP thất bại ({response.status_code}): {response.text[:1000]}"
            ) from exc
        text_parts: list[str] = []
        tool_calls: list[str] = []
        for raw_line in response.iter_lines(decode_unicode=True):
            line = raw_line.decode() if isinstance(raw_line, bytes) else (raw_line or "")
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            if event_type == "response.output_text.delta":
                text_parts.append(event.get("delta", ""))
            elif event_type == "response.output_item.added":
                item = event.get("item") or {}
                if item.get("type") == "mcp_call":
                    name = item.get("name") or "exa"
                    if name not in tool_calls:
                        tool_calls.append(name)
                    if on_tool:
                        on_tool(name)
            elif event_type in {"response.failed", "response.mcp_call.failed"}:
                raise ResearchOutputError(f"Exa research failed: {event.get('error') or event}")
        text = "".join(text_parts).strip()
        if not text:
            raise ResearchOutputError("Exa research không trả về nội dung")
        if not tool_calls:
            raise ResearchOutputError("Exa MCP không được gọi trong bước nghiên cứu")
        if required_tool and not any(required_tool in name for name in tool_calls):
            raise ResearchOutputError(
                f"Bắt buộc gọi {required_tool}, nhưng Exa chỉ gọi: {tool_calls}"
            )
        if not re.search(r"https?://", text):
            raise ResearchOutputError("Báo cáo Exa không chứa URL nguồn")
        return text, tool_calls
