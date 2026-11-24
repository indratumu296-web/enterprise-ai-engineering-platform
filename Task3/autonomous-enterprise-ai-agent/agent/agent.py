from __future__ import annotations

from typing import Any

from agent.planner import Plan
from tools.crm import update_lead
from tools.inventory import lookup_inventory
from tools.tickets import create_support_ticket


def execute_plan(plan: Plan, api_base_url: str, approved: bool = False) -> dict[str, Any]:
    if plan.needs_input:
        raise ValueError(plan.needs_input)
    if plan.tool in {"update_lead_status", "create_support_ticket"} and not approved:
        return {
            "pending_approval": True,
            "message": "This write operation requires explicit approval before execution.",
        }
    if plan.tool == "lookup_inventory":
        return lookup_inventory(str(plan.arguments["product"]), api_base_url)
    if plan.tool == "update_lead_status":
        return update_lead(
            str(plan.arguments["lead_id"]),
            str(plan.arguments["status"]),
            api_base_url,
        )
    if plan.tool == "create_support_ticket":
        return create_support_ticket(
            str(plan.arguments["customer"]),
            str(plan.arguments["issue"]),
            api_base_url,
        )
    raise ValueError("The requested action is not supported.")