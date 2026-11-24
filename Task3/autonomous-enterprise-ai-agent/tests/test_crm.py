def test_update_lead_status(client):
    response = client.patch("/leads/L101", json={"status": "Contacted"})

    assert response.status_code == 200
    assert response.json() == {"lead_id": "L101", "customer": "Rahul", "status": "Contacted"}


def test_invalid_lead_status_is_rejected(client):
    response = client.patch("/leads/L101", json={"status": "Spam"})

    assert response.status_code == 422


def test_unknown_lead_is_not_found(client):
    response = client.patch("/leads/L999", json={"status": "Lost"})

    assert response.status_code == 404