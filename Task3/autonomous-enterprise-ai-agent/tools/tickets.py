from uuid import uuid4

from utils.retry import request_json


def create_support_ticket(customer: str, issue: str, api_base_url: str) -> dict:
    idempotency_key = str(uuid4())
    ticket = request_json(
        "POST",
        f"{api_base_url.rstrip('/')}/tickets",
        json={"customer": customer, "issue": issue},
        headers={"Idempotency-Key": idempotency_key},
    )
    return {
        "message": (
            f"Created ticket {ticket['ticket_id']} for {ticket['customer']}. "
            f"Status: {ticket['status']}."
        ),
        "ticket": ticket,
    }