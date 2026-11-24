def test_create_ticket(client):
    response = client.post(
        "/tickets",
        json={"customer": "Mina", "issue": "Cannot reset password"},
    )

    assert response.status_code == 201
    assert response.json()["customer"] == "Mina"
    assert response.json()["issue"] == "Cannot reset password"
    assert response.json()["status"] == "Open"
    assert response.json()["ticket_id"].startswith("TKT-")


def test_ticket_fields_are_validated(client):
    response = client.post("/tickets", json={"customer": "", "issue": "No"})

    assert response.status_code == 422


def test_ticket_fields_are_trimmed_before_validation(client):
    response = client.post("/tickets", json={"customer": "  ", "issue": "   "})

    assert response.status_code == 422


def test_ticket_creation_is_idempotent_for_retries(client):
    headers = {"Idempotency-Key": "repeatable-ticket-request"}
    payload = {"customer": "Mina", "issue": "Cannot reset password"}

    first = client.post("/tickets", json=payload, headers=headers)
    retry = client.post("/tickets", json=payload, headers=headers)

    assert first.status_code == retry.status_code == 201
    assert first.json() == retry.json()
    assert len(client.get("/tickets").json()) == 1