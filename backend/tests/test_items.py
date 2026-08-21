from fastapi.testclient import TestClient


def test_create_and_get_item(client: TestClient):
    """Test creating an item and then retrieving it."""
    # 1. Create item
    create_payload = {
        "title": "Clean Architecture Item",
        "description": "Testing layered structure",
        "is_completed": False,
    }
    create_res = client.post("/api/items", json=create_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["success"] is True
    item_id = created_data["data"]["id"]
    assert created_data["data"]["title"] == "Clean Architecture Item"

    # 2. Get item by ID
    get_res = client.get(f"/api/items/{item_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == item_id

    # 3. Update item
    update_res = client.patch(f"/api/items/{item_id}", json={"is_completed": True})
    assert update_res.status_code == 200
    assert update_res.json()["data"]["is_completed"] is True

    # 4. List items
    list_res = client.get("/api/items")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 5. Delete item
    del_res = client.delete(f"/api/items/{item_id}")
    assert del_res.status_code == 200

    # 6. Verify 404 after deletion
    not_found_res = client.get(f"/api/items/{item_id}")
    assert not_found_res.status_code == 404
