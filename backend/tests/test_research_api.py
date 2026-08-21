import json
from pathlib import Path

from app.api.v1.endpoints import research as research_endpoint


def _g7_payload():
    workspace = Path(__file__).resolve().parents[2]
    return json.loads(
        (workspace / "sample_data/05_trung_nguyen_g7/research_input.json").read_text(encoding="utf-8")
    )


def _g7_multipart(payload=None):
    payload = payload or _g7_payload()
    data = {
        "schema_version": payload["schema_version"],
        "campaign_id": payload["campaign_id"],
        "product_brief": json.dumps(payload["product_brief"]),
        "brand_kit": json.dumps(payload["brand_kit"]),
        "audience_brief": json.dumps(payload["audience_brief"]),
        "market_signal": json.dumps(payload["market_signal"]),
    }
    files = [
        ("logo", ("logo.png", b"fake-logo", "image/png")),
        ("product_photos", ("product_01.jpg", b"fake-product-1", "image/jpeg")),
        ("product_photos", ("product_02.jpg", b"fake-product-2", "image/jpeg")),
    ]
    return data, files


def test_research_run_accepts_g7_contract_and_returns_frontend_payload(client, monkeypatch):
    captured = {}

    def fake_run(**kwargs):
        captured.update(kwargs)
        return {
            "campaign_id": "trung-nguyen-g7-cross-border-9-9",
            "engine": "exa_specialists",
            "status": "completed",
            "plan": {"schema_version": "1.0", "creative_routes": [{"route_name": "A"}, {"route_name": "B"}]},
            "sources": ["https://example.com/research"],
            "research_tool_calls": ["web_search_exa", "web_fetch_exa"],
            "input_assets": [{
                "label": "logo", "source": "sample_data/logo.png",
                "transport": "base64_data_url", "mime_type": "image/png", "bytes": 42,
            }],
        }

    monkeypatch.setattr(research_endpoint.research_service, "run", fake_run)
    data, files = _g7_multipart()
    response = client.post("/api/research/run", data=data, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["creative_routes"][0]["route_name"] == "A"
    assert captured["research_input"]["brand_kit"]["product_photos"] == ["product_01.jpg", "product_02.jpg"]
    image_urls, manifest = captured["visual_assets"]
    assert len(image_urls) == 3
    assert all(url.startswith("data:image/") for url in image_urls)
    assert [item["source"] for item in manifest] == ["logo.png", "product_01.jpg", "product_02.jpg"]


def test_research_run_rejects_unknown_campaign_objective(client):
    payload = _g7_payload()
    payload["market_signal"]["campaign_objectives"] = ["make_it_viral"]
    data, files = _g7_multipart(payload)
    response = client.post("/api/research/run", data=data, files=files)
    assert response.status_code == 400
    assert response.json()["success"] is False
