from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from agent.agent import execute_plan
from agent.planner import Plan, plan_request
from utils.retry import APIRequestError, request_json

load_dotenv(Path(__file__).resolve().parent / ".env")

st.set_page_config(
    page_title="Datheon Enterprise Agent",
    page_icon=":material/hub:",
    layout="wide",
)


@st.cache_data(ttl=5)
def get_api_data(base_url: str, resource: str) -> Any:
    return request_json("GET", f"{base_url.rstrip('/')}/{resource.lstrip('/')}")


def initialize_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("execution_history", [])
    st.session_state.setdefault("pending_approval", None)
    st.session_state.setdefault("api_base_url", os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))


def append_message(role: str, content: str, timeline: list[dict[str, str]] | None = None) -> None:
    message: dict[str, Any] = {"role": role, "content": content}
    if timeline:
        message["timeline"] = timeline
    st.session_state.messages.append(message)


def render_chat() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("timeline"):
                with st.expander("Thought / action / observation"):
                    for step in message["timeline"]:
                        st.markdown(f"**{step['label']}**  \n{step['detail']}")


def record_result(plan: Plan, result: dict[str, Any], outcome: str) -> None:
    st.session_state.execution_history.insert(
        0,
        {
            "time": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "action": plan.summary,
            "tool": plan.tool or "unmatched",
            "outcome": outcome,
            "result": result,
        },
    )


def execute_approved_plan(plan: Plan, base_url: str) -> None:
    try:
        result = execute_plan(plan, base_url, approved=True)
        observation = result.get("message", "The operation completed.")
        outcome = "Success"
        timeline = [
            {"label": "Thought", "detail": f"Matched the request to {plan.tool.replace('_', ' ')}."},
            {"label": "Action", "detail": plan.summary},
            {"label": "Observation", "detail": observation},
        ]
        append_message("assistant", observation, timeline)
        record_result(plan, result, outcome)
    except (APIRequestError, ValueError) as exc:
        message = f"The operation could not be completed: {exc}"
        append_message(
            "assistant",
            message,
            [{"label": "Observation", "detail": str(exc)}],
        )
        record_result(plan, {"error": str(exc)}, "Failed")
    finally:
        st.session_state.pending_approval = None
        get_api_data.clear()


initialize_state()
base_url = st.sidebar.text_input(
    "Mock API address",
    key="api_base_url",
    help="FastAPI service address (default: http://127.0.0.1:8000).",
).rstrip("/")
st.sidebar.caption("Use the mock API only with sample business data.")
try:
    health = get_api_data(base_url, "health")
    st.sidebar.success(f"API online - {health.get('status', 'healthy')}")
except APIRequestError as exc:
    st.sidebar.error("Mock API is offline.")
    st.sidebar.caption(str(exc))

st.title("Enterprise AI agent")
st.caption("A tool-calling assistant for inventory, sales leads, and customer support.")

agent_tab, inventory_tab, leads_tab, tickets_tab, history_tab = st.tabs(
    ["Agent", "Inventory", "Leads", "Tickets", "Execution history"]
)

with agent_tab:
    st.markdown("Ask for a business operation in plain language. Changes are held for your approval.")
    if not st.session_state.messages:
        st.info(
            "Try: 'Check stock for laptop', 'Update lead L101 to Contacted', "
            "or 'Create a ticket for Rahul about a payment issue.'"
        )

    pending: Plan | None = st.session_state.pending_approval
    if pending is not None:
        with st.container(border=True):
            st.warning("Approval required", icon=":material/approval:")
            st.write(pending.summary)
            st.json(pending.arguments)
            approve_col, reject_col = st.columns(2)
            if approve_col.button(
                "Approve and execute",
                type="primary",
                icon=":material/check:",
                key="approve_operation",
            ):
                execute_approved_plan(pending, base_url)
                st.rerun()
            if reject_col.button(
                "Reject",
                icon=":material/close:",
                key="reject_operation",
            ):
                append_message(
                    "assistant",
                    "The operation was rejected. No business data was changed.",
                    [{"label": "Observation", "detail": "Approval was declined; the API was not called."}],
                )
                record_result(pending, {"cancelled": True}, "Rejected")
                st.session_state.pending_approval = None
                st.rerun()

    render_chat()
    prompt = st.chat_input("What would you like the agent to do?")
    if prompt:
        append_message("user", prompt)
        try:
            plan = plan_request(prompt)
            if plan.tool is None:
                append_message(
                    "assistant",
                    plan.needs_input or "I couldn't identify a supported operation. Try an inventory lookup, lead update, or ticket creation.",
                )
                record_result(plan, {"message": plan.needs_input}, "Needs input")
            elif plan.needs_input:
                append_message(
                    "assistant",
                    plan.needs_input,
                    [{"label": "Thought", "detail": f"Selected {plan.tool.replace('_', ' ')} and checked its required fields."}],
                )
                record_result(plan, {"message": plan.needs_input}, "Needs input")
            elif plan.requires_approval:
                st.session_state.pending_approval = plan
                append_message(
                    "assistant",
                    "I prepared this change. Review the details above and approve it before I call the API.",
                    [{"label": "Thought", "detail": f"Selected {plan.tool.replace('_', ' ')}; this is a write operation."},
                     {"label": "Action", "detail": plan.summary},
                     {"label": "Observation", "detail": "Waiting for explicit human approval; no write has run yet."}],
                )
            else:
                try:
                    result = execute_plan(plan, base_url, approved=False)
                    observation = result.get("message", "The lookup completed.")
                    append_message(
                        "assistant",
                        observation,
                        [{"label": "Thought", "detail": f"Selected {plan.tool.replace('_', ' ')}; this is a read-only operation."},
                         {"label": "Action", "detail": plan.summary},
                         {"label": "Observation", "detail": observation}],
                    )
                    record_result(plan, result, "Success")
                    get_api_data.clear()
                except (APIRequestError, ValueError) as exc:
                    append_message(
                        "assistant",
                        f"The operation could not be completed: {exc}",
                        [{"label": "Observation", "detail": str(exc)}],
                    )
                    record_result(plan, {"error": str(exc)}, "Failed")
        except (APIRequestError, ValueError, RuntimeError) as exc:
            append_message("assistant", f"I couldn't plan that request: {exc}")
        st.rerun()

with inventory_tab:
    st.subheader("Inventory")
    try:
        inventory = get_api_data(base_url, "inventory")
        if inventory:
            st.dataframe(inventory, hide_index=True)
        else:
            st.info("No inventory records were returned.")
    except APIRequestError as exc:
        st.error(f"Inventory could not be loaded: {exc}")

with leads_tab:
    st.subheader("CRM leads")
    try:
        leads = get_api_data(base_url, "leads")
        if leads:
            st.dataframe(leads, hide_index=True)
        else:
            st.info("No leads were returned.")
        st.caption("Lead status changes are available through the agent and require approval.")
    except APIRequestError as exc:
        st.error(f"Leads could not be loaded: {exc}")

with tickets_tab:
    st.subheader("Support tickets")
    try:
        tickets = get_api_data(base_url, "tickets")
        if tickets:
            st.dataframe(tickets, hide_index=True)
        else:
            st.info("No support tickets have been created.")
        st.caption("Ticket creation is available through the agent and requires approval.")
    except APIRequestError as exc:
        st.error(f"Tickets could not be loaded: {exc}")

with history_tab:
    st.subheader("Execution history")
    if st.session_state.execution_history:
        st.dataframe(
            [
                {
                    "Time": item["time"],
                    "Action": item["action"],
                    "Tool": item["tool"],
                    "Outcome": item["outcome"],
                }
                for item in st.session_state.execution_history
            ],
            hide_index=True,
        )
        for item in st.session_state.execution_history:
            with st.expander(f"{item['time']} · {item['action']} · {item['outcome']}"):
                st.json(item["result"])
    else:
        st.info("Actions from this browser session will appear here.")
