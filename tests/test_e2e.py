def test_user_journey_add_list_delete_dish(client):
    # 1) initial state should contain seeded dishes
    resp = client.get("/dishes")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 3  

    # 2) add a new dish
    new_dish = {"id": 999, "dish": "Pizza", "country": "Italy"}
    resp = client.post("/dishes", json=new_dish)
    assert resp.status_code == 201
    created = resp.get_json()
    assert created["status"] == "ADDED"
    assert created["id"] == 999

    # 3) verify it appears in list
    resp = client.get("/dishes")
    assert resp.status_code == 200
    dishes = resp.get_json()
    assert any(d["id"] == 999 and d["dish"] == "Pizza" and d["country"] == "Italy" for d in dishes)

    # 4) delete it
    resp = client.delete("/dishes/999")
    assert resp.status_code == 200
    deleted = resp.get_json()
    assert deleted["status"] == "DELETED"
    assert deleted["id"] == 999

    # 5) verify it is gone
    resp = client.get("/dishes")
    assert resp.status_code == 200
    dishes = resp.get_json()
    assert all(d["id"] != 999 for d in dishes)


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.data.decode("utf-8") == "OK"
