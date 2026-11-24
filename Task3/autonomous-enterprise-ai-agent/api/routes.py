from fastapi import APIRouter, Header, HTTPException, Query

from Database import db
from api.schemas import LeadStatusUpdate, TicketCreate

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/inventory")
def inventory(search: str | None = Query(default=None, max_length=100)) -> list[dict]:
    return db.get_inventory(search)


@router.get("/leads")
def leads() -> list[dict]:
    return db.get_leads()


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: str, update: LeadStatusUpdate) -> dict:
    lead = db.update_lead(lead_id, update.status)
    if lead is None:
        raise HTTPException(status_code=404, detail=f"Lead '{lead_id}' was not found.")
    return lead


@router.get("/tickets")
def tickets() -> list[dict]:
    return db.get_tickets()


@router.post("/tickets", status_code=201)
def create_ticket(
    ticket: TicketCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
) -> dict:
    return db.create_ticket(ticket.customer, ticket.issue, idempotency_key)