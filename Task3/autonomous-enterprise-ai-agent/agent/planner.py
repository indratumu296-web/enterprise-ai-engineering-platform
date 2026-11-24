from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

ALLOWED_LEAD_STATUSES = {"New", "Contacted", "Qualified", "Converted", "Lost"}


@dataclass
class Plan:
    tool: str | None
    arguments: dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    requires_approval: bool = False
    needs_input: str | None = None


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_inventory",
            "description": "Look up product stock by product name or product ID.",
            "parameters": {
                "type": "object",
                "properties": {"product": {"type": "string", "description": "Product name or ID"}},
                "required": ["product"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_lead_status",
            "description": "Update a CRM lead's status. This is a sensitive write operation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string", "description": "Lead ID, such as L101"},
                    "status": {"type": "string", "enum": sorted(ALLOWED_LEAD_STATUSES)},
                },
                "required": ["lead_id", "status"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support ticket. This is a sensitive write operation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer": {"type": "string"},
                    "issue": {"type": "string"},
                },
                "required": ["customer", "issue"],
                "additionalProperties": False,
            },
        },
    },
]


def _clean_entity(value: str) -> str:
    value = re.split(r"\b(?:please|and then|then)\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    value = value.strip(" \t\r\n.,!?\"'`")
    return re.sub(r"^customer\s+", "", value, flags=re.IGNORECASE)


def _inventory_product(request: str) -> str:
    match = re.search(
        r"\b(?:stock|inventory|availability)\s+(?:of|for)\s+(?:the\s+)?(.+)$",
        request,
        re.IGNORECASE,
    )
    if match:
        return _clean_entity(match.group(1))
    match = re.search(r"\b(?:of|for)\s+(?:the\s+)?(.+)$", request, re.IGNORECASE)
    if match:
        return _clean_entity(match.group(1))
    ignored = r"\b(?:check|show|find|look up|lookup|stock|inventory|availability|available|please|how many|is there|any)\b"
    return _clean_entity(re.sub(ignored, "", request, flags=re.IGNORECASE))


def _local_plan(request: str) -> Plan:
    text = request.strip()
    lowered = text.lower()

    if any(word in lowered for word in ("ticket", "support case", "support request")):
        customer_match = re.search(
            r"\bfor\s+(.+?)(?=\s+\b(?:about|regarding|issue|problem)\b|$)",
            text,
            re.IGNORECASE,
        )
        issue_match = re.search(r"\b(?:about|regarding|issue|problem)\s*:?\s*(.+)$", text, re.IGNORECASE)
        customer = _clean_entity(customer_match.group(1)) if customer_match else ""
        issue = _clean_entity(issue_match.group(1)) if issue_match else ""
        missing = []
        if not customer:
            missing.append("the customer name")
        if len(issue) < 3:
            missing.append("a short description of the issue")
        if missing:
            return Plan(
                "create_support_ticket",
                {"customer": customer, "issue": issue},
                "Create a support ticket",
                True,
                "Please provide " + " and ".join(missing) + " (for example: 'Create a ticket for Rahul about a payment issue').",
            )
        return Plan(
            "create_support_ticket",
            {"customer": customer, "issue": issue},
            f"Create a support ticket for {customer}",
            True,
        )

    if any(word in lowered for word in ("lead", "customer")) and any(
        word in lowered for word in ("update", "change", "set", "mark", "move")
    ):
        status = next(
            (candidate for candidate in ALLOWED_LEAD_STATUSES if re.search(rf"\b{candidate}\b", text, re.IGNORECASE)),
            None,
        )
        lead_match = re.search(r"\bL\d+\b", text, re.IGNORECASE)
        if not lead_match:
            lead_match = re.search(
                r"\bfor\s+([A-Za-z][A-Za-z .'-]*?)(?=\s+\b(?:to|as|status|with)\b|$)",
                text,
                re.IGNORECASE,
            )
        if not lead_match:
            lead_match = re.search(
                r"\b(?:lead|customer)\s+(?!status\b)(?:named\s+)?([A-Za-z][A-Za-z .'-]*?)(?=\s+\b(?:to|as|status|with)\b|$)",
                text,
                re.IGNORECASE,
            )
        lead_id = (
            lead_match.group(0)
            if lead_match and re.fullmatch(r"L\d+", lead_match.group(0), re.IGNORECASE)
            else _clean_entity(lead_match.group(1)) if lead_match else ""
        )
        missing = []
        if not lead_id:
            missing.append("the lead ID or customer name")
        if not status:
            missing.append("the new status (New, Contacted, Qualified, Converted, or Lost)")
        if missing:
            return Plan(
                "update_lead_status",
                {"lead_id": lead_id, "status": status or ""},
                "Update a CRM lead",
                True,
                "Please provide " + " and ".join(missing) + ".",
            )
        return Plan(
            "update_lead_status",
            {"lead_id": lead_id, "status": status},
            f"Change lead {lead_id} to {status}",
            True,
        )

    if any(word in lowered for word in ("stock", "inventory", "availability", "how many")):
        product = _inventory_product(text)
        if not product:
            return Plan(
                "lookup_inventory",
                {"product": ""},
                "Look up product inventory",
                needs_input="Which product should I look up?",
            )
        return Plan("lookup_inventory", {"product": product}, f"Check stock for {product}")

    return Plan(None, needs_input="I can look up inventory, update a lead status, or create a support ticket.")


def _openai_plan(request: str) -> Plan:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OPENAI_API_KEY is set, but the openai package is not installed.") from exc

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Choose exactly one enterprise tool for the user's request. "
                    "Extract only facts provided by the user. Do not execute tools. "
                    "Writes are subject to human approval."
                ),
            },
            {"role": "user", "content": request},
        ],
        tools=TOOL_DEFINITIONS,
        tool_choice="required",
    )
    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise ValueError("The AI planner did not select a supported operation.")
    selected = tool_calls[0].function
    try:
        arguments = json.loads(selected.arguments)
    except json.JSONDecodeError as exc:
        raise ValueError("The AI planner returned invalid tool arguments.") from exc
    tool = selected.name
    if tool == "lookup_inventory":
        product = str(arguments.get("product", "")).strip()
        if not product:
            return Plan(tool, arguments, "Look up product inventory", needs_input="Which product should I look up?")
        return Plan(tool, {"product": product}, f"Check stock for {product}")
    if tool == "update_lead_status":
        lead_id = str(arguments.get("lead_id", "")).strip()
        status = str(arguments.get("status", "")).strip().title()
        if not lead_id or status not in ALLOWED_LEAD_STATUSES:
            return Plan(
                tool,
                {"lead_id": lead_id, "status": status},
                "Update a CRM lead",
                True,
                "Please provide a lead ID or customer name and a valid new lead status.",
            )
        return Plan(tool, {"lead_id": lead_id, "status": status}, f"Change lead {lead_id} to {status}", True)
    if tool == "create_support_ticket":
        customer = str(arguments.get("customer", "")).strip()
        issue = str(arguments.get("issue", "")).strip()
        missing = []
        if not customer:
            missing.append("the customer name")
        if len(issue) < 3:
            missing.append("a short description of the issue")
        return Plan(
            tool,
            {"customer": customer, "issue": issue},
            f"Create a support ticket for {customer or 'the customer'}",
            True,
            "Please provide " + " and ".join(missing) + "." if missing else None,
        )
    raise ValueError(f"The AI planner selected an unsupported tool: {tool}")


def plan_request(request: str) -> Plan:
    if not request.strip():
        return Plan(None, needs_input="Please describe the business operation you want to perform.")
    plan = _openai_plan(request) if os.getenv("OPENAI_API_KEY") else _local_plan(request)
    if plan.tool == "update_lead_status":
        status = str(plan.arguments.get("status", "")).title()
        if status and status not in ALLOWED_LEAD_STATUSES:
            raise ValueError(f"Unsupported lead status: {status}")
    return plan