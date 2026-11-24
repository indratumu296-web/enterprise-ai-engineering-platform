def test_inventory_search_matches_product_name(client):
    response = client.get("/inventory", params={"search": "laptop"})

    assert response.status_code == 200
    assert {item["product_id"] for item in response.json()} == {"P101", "P102", "P103"}


def test_inventory_search_matches_product_id(client):
    response = client.get("/inventory", params={"search": "P104"})

    assert response.status_code == 200
    assert response.json() == [
        {"product_id": "P104", "product_name": "Wireless Mouse", "quantity": 42}
    ]