import json
from pathlib import Path

from run import mcp_tool, payload


def test_exa_project_config_is_present():
    config_path = Path(__file__).resolve().parents[2] / ".mcp.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert config["mcpServers"]["exa"]["url"] == "https://mcp.exa.ai/mcp"


def test_exa_translates_to_modelark_mcp_tool_shape():
    tool = mcp_tool("exa")

    assert tool == {
        "type": "mcp",
        "server_label": "exa",
        "server_url": "https://mcp.exa.ai/mcp",
        "require_approval": "never",
    }
    assert payload("search for evidence", [tool])["tools"] == [tool]
