def test_get_dishes_returns_seeded_data(client):
    res = client.get("/dishes")
    assert res.status_code == 200

    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) >= 3

    # Check one known seeded row exists (from init.sql)
    dishes = {(d["id"], d["dish"], d["country"]) for d in data}
    assert (1, "Ceviche", "Peru") in dishes


def test_post_dishes_adds_new_item(client):
    payload = {"id": 10, "dish": "Pizza", "country": "Italy"}
    res = client.post("/dishes", json=payload)
    assert res.status_code == 201

    body = res.get_json()
    assert body["status"] == "ADDED"
    assert body["id"] == 10
    assert body["dish"] == "Pizza"
    assert body["country"] == "Italy"

    # Verify it is now present in GET /dishes
    res2 = client.get("/dishes")
    data2 = res2.get_json()
    assert any(d["id"] == 10 and d["dish"] == "Pizza" for d in data2)


def test_post_dishes_missing_id_returns_400(client):
    res = client.post("/dishes", json={"dish": "Sushi", "country": "Japan"})
    assert res.status_code == 400
    assert "Missing field: id" in res.get_json()["error"]


def test_post_dishes_empty_dish_returns_400(client):
    res = client.post("/dishes", json={"id": 11, "dish": "   ", "country": "Japan"})
    assert res.status_code == 400
    assert "dish" in res.get_json()["error"].lower()


def test_post_dishes_non_int_id_returns_400(client):
    res = client.post(
        "/dishes", json={"id": "abc", "dish": "Sushi", "country": "Japan"}
    )
    assert res.status_code == 400
    assert "must be an integer" in res.get_json()["error"]


def test_delete_dish_existing_returns_200(client):
    # Seeded id=2 exists (Tacos)
    res = client.delete("/dishes/2")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "DELETED"
    assert body["id"] == 2

    # Verify it's gone
    res2 = client.get("/dishes")
    data2 = res2.get_json()
    assert all(d["id"] != 2 for d in data2)


def test_delete_dish_not_found_returns_404(client):
    res = client.delete("/dishes/9999")
    assert res.status_code == 404
    assert res.get_json()["error"] == "Not found"
