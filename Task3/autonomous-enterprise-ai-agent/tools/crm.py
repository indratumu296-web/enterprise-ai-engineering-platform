from utils.retry import request_json


def update_lead(lead_reference: str, status: str, api_base_url: str) -> dict:
    leads = request_json("GET", f"{api_base_url.rstrip('/')}/leads")
    matches = [
        lead
        for lead in leads
        if lead["lead_id"].casefold() == lead_reference.casefold()
        or lead["customer"].casefold() == lead_reference.casefold()
    ]
    if not matches:
        raise ValueError(f"No lead matched '{lead_reference}'.")
    if len(matches) > 1:
        raise ValueError(f"More than one lead matched '{lead_reference}'; use a lead ID.")
    updated = request_json(
        "PATCH",
        f"{api_base_url.rstrip('/')}/leads/{matches[0]['lead_id']}",
        json={"status": status},
    )
    return {
        "message": f"Updated {updated['customer']} ({updated['lead_id']}) to {updated['status']}.",
        "lead": updated,
    }