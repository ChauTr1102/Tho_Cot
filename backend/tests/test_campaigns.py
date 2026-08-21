from fastapi.testclient import TestClient


def test_campaign_crud_and_listing(client: TestClient):
    created = client.post(
        "/api/campaigns",
        json={"id": "campaign-1", "name": "Launch campaign", "description": "Initial brief"},
    )
    assert created.status_code == 201
    assert created.json()["data"]["status"] == "draft"

    listed = client.get("/api/campaigns")
    assert listed.status_code == 200
    assert listed.json()["data"] == [
        {
            "id": "campaign-1",
            "name": "Launch campaign",
            "description": "Initial brief",
            "status": "draft",
            "has_research_result": False,
            "created_at": created.json()["data"]["created_at"],
            "updated_at": created.json()["data"]["updated_at"],
        }
    ]

    updated = client.patch("/api/campaigns/campaign-1", json={"name": "Updated launch"})
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Updated launch"

    fetched = client.get("/api/campaigns/campaign-1")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["research_result"] is None

    assert client.delete("/api/campaigns/campaign-1").status_code == 200
    assert client.get("/api/campaigns/campaign-1").status_code == 404


def test_campaign_id_must_be_unique(client: TestClient):
    payload = {"id": "duplicate", "name": "Campaign"}
    assert client.post("/api/campaigns", json=payload).status_code == 201
    response = client.post("/api/campaigns", json=payload)
    assert response.status_code == 400
    assert response.json()["success"] is False

