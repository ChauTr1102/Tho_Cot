import pytest
from fastapi.testclient import TestClient

from app.storage.campaign_store import campaign_store as campaign_store_instance


@pytest.fixture(autouse=True)
def isolate_campaign_store(tmp_path, monkeypatch):
    """Redirect the JSON campaign store to a temp dir so tests don't write into backend/data."""
    monkeypatch.setattr(campaign_store_instance, "root", tmp_path)


def _sample_payload() -> dict:
    return {
        "campaign_id": "camp-api-test-1",
        "product_brief": {
            "product_name": "Ruby Serum",
            "category": "Skincare",
            "key_selling_points": ["Brightens skin", "Fast absorbing"],
            "target_market": "Vietnam",
            "required_claims": [],
            "forbidden_claims": [],
        },
        "brand_kit": {"tone_of_voice": "friendly"},
        "audience_brief": {
            "target_customer": "Women 20-35 interested in skincare",
            "language": "vi",
            "platform": ["TikTok Shop"],
            "market": "VN",
        },
        "market_signal": {
            "consumer_pain_point": "dull skin",
            "sources": ["ref://trend"],
        },
    }


def test_run_campaign_and_get_latest_qa(client: TestClient):
    run_res = client.post("/api/campaigns/run", json=_sample_payload())
    assert run_res.status_code == 201
    run_data = run_res.json()
    assert run_data["success"] is True
    assert run_data["data"]["campaign_id"] == "camp-api-test-1"
    assert run_data["data"]["passed"] is True

    qa_res = client.get("/api/campaigns/camp-api-test-1/qa")
    assert qa_res.status_code == 200
    qa_data = qa_res.json()
    assert qa_data["success"] is True
    assert qa_data["data"]["campaign_id"] == "camp-api-test-1"


def test_get_latest_qa_404_when_campaign_unknown(client: TestClient):
    res = client.get("/api/campaigns/does-not-exist/qa")
    assert res.status_code == 404
    assert res.json()["success"] is False
