from agent.agent import execute_plan
from agent.planner import plan_request


def test_plans_inventory_lookup():
    plan = plan_request("Check stock for laptop")

    assert plan.tool == "lookup_inventory"
    assert plan.arguments == {"product": "laptop"}
    assert not plan.requires_approval


def test_plans_lead_update_for_approval():
    plan = plan_request("Update lead L101 to Contacted")

    assert plan.tool == "update_lead_status"
    assert plan.arguments == {"lead_id": "L101", "status": "Contacted"}
    assert plan.requires_approval


def test_plans_customer_lead_update_using_status_phrase():
    plan = plan_request("Update lead status for Rahul to Qualified")

    assert plan.arguments == {"lead_id": "Rahul", "status": "Qualified"}


def test_ticket_plan_requests_missing_details():
    plan = plan_request("Create a support ticket")

    assert plan.tool == "create_support_ticket"
    assert plan.needs_input


def test_write_cannot_execute_without_approval():
    plan = plan_request("Update lead L101 to Qualified")

    result = execute_plan(plan, "http://127.0.0.1:8000")

    assert result["pending_approval"] is True