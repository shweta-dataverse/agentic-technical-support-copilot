"""Internal support-engineer console.

Thin client over the FastAPI service, zero business logic here. Everything it
shows comes from the versioned HTTP API, which is the point: any frontend team
could build this same console from /openapi.json.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import streamlit as st

API_URL = os.environ.get("COPILOT_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("COPILOT_API_KEY", "dev-key-change-me")

st.set_page_config(page_title="Support Copilot", page_icon="🛠", layout="wide")

_SEVERITY_COLOR = {
    "critical": "#b71c1c",
    "high": "#e64a19",
    "medium": "#f9a825",
    "low": "#2e7d32",
}
_STATUS_COLOR = {"open": "#1565c0", "resolved": "#2e7d32", "escalated": "#b71c1c"}

st.markdown(
    """
    <style>
      .pill {display:inline-block; padding:2px 10px; border-radius:12px;
             color:white; font-size:0.75rem; font-weight:600; letter-spacing:.02em;}
      .muted {color:#8a8a8a; font-size:0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def api(method: str, path: str, **kwargs: Any) -> httpx.Response:
    return httpx.request(
        method, f"{API_URL}{path}", headers={"X-API-Key": API_KEY}, timeout=120.0, **kwargs
    )


def pill(text: str, color: str) -> str:
    return f'<span class="pill" style="background:{color}">{text}</span>'


def render_resolution(result: dict[str, Any]) -> None:
    confidence = float(result.get("confidence", 0.0))
    if result.get("escalate"):
        st.error(f"⚠️ Needs human review — the copilot escalated (confidence {confidence:.2f}).")
    else:
        st.success(f"✅ Grounded resolution (confidence {confidence:.2f})")
    st.progress(confidence, text=f"confidence {confidence:.2f}")

    st.markdown("##### Resolution steps")
    for i, step in enumerate(result.get("resolution_steps", []), 1):
        st.markdown(f"**{i}.** {step}")

    citations = result.get("citations", [])
    if citations:
        st.markdown("##### Citations")
        for c in citations:
            with st.expander(f"📄 {c['doc']} — page {c['page']}"):
                st.markdown(f"> {c.get('quote_span', '')}")
    if result.get("reasoning_summary"):
        st.caption(f"Reasoning: {result['reasoning_summary']}")
    if result.get("cost_eur") is not None:
        st.caption(f"Resolution cost: €{result['cost_eur']:.4f}")


# --- header ----------------------------------------------------------------

left, right = st.columns([0.7, 0.3])
with left:
    st.title("🛠 Support Copilot")
    st.caption("Siemens SIMATIC S7-1500 · internal support console")
with right:
    if st.button("↻ Refresh queue", use_container_width=True):
        st.rerun()

# --- load the queue --------------------------------------------------------

try:
    tickets: list[dict[str, Any]] = api("GET", "/v1/tickets").json()
except Exception as exc:  # noqa: BLE001 — surface connectivity issues to the user
    st.error(f"Cannot reach the API at {API_URL}: {exc}")
    st.stop()

if not tickets:
    st.info("The ticket queue is empty.")
    if st.button("Load sample tickets"):
        api("POST", "/v1/tickets/seed")
        st.rerun()
    st.stop()

# --- KPIs ------------------------------------------------------------------

total = len(tickets)
resolved = sum(1 for t in tickets if t["resolved"])
open_count = sum(1 for t in tickets if t["status"] == "open")
critical = sum(1 for t in tickets if t["severity"] == "critical")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Tickets", total)
k2.metric("Open", open_count)
k3.metric("Resolved", resolved)
k4.metric("Critical", critical)

st.divider()
queue_col, detail_col = st.columns([0.42, 0.58], gap="large")

# --- queue -----------------------------------------------------------------

with queue_col:
    st.markdown("### Ticket queue")
    if "selected" not in st.session_state:
        st.session_state.selected = tickets[0]["ticket_id"]
    for t in tickets:
        sev = t.get("severity") or "low"
        badges = (
            pill(sev, _SEVERITY_COLOR.get(sev, "#607d8b"))
            + " "
            + pill(
                "resolved" if t["resolved"] else t["status"],
                _STATUS_COLOR.get("resolved" if t["resolved"] else t["status"], "#607d8b"),
            )
        )
        with st.container(border=True):
            st.markdown(
                f"**{t['ticket_id']}** &nbsp; {badges}<br>{t['summary']}",
                unsafe_allow_html=True,
            )
            if st.button("Open", key=f"open-{t['ticket_id']}", use_container_width=True):
                st.session_state.selected = t["ticket_id"]
                st.rerun()

    st.divider()
    with st.expander("➕ Submit a new ticket"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        if st.button("Resolve new ticket") and title and desc:
            with st.spinner("Agents working…"):
                resp = api("POST", "/v1/resolve", json={"title": title, "description": desc})
            if resp.status_code == 200:
                st.session_state.new_result = resp.json()
                st.rerun()
            else:
                st.error(resp.text)

# --- detail ----------------------------------------------------------------

with detail_col:
    if st.session_state.get("new_result"):
        st.markdown("### New ticket resolution")
        render_resolution(st.session_state.pop("new_result"))
        st.stop()

    ticket_id = st.session_state.selected
    ticket = api("GET", f"/v1/tickets/{ticket_id}").json()
    sev = ticket.get("severity") or "low"
    st.markdown(f"### {ticket_id}")
    st.markdown(
        pill(sev, _SEVERITY_COLOR.get(sev, "#607d8b"))
        + " "
        + pill(ticket["status"], _STATUS_COLOR.get(ticket["status"], "#607d8b"))
        + f" &nbsp; <span class='muted'>{ticket.get('category', '')}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(f"**{ticket['summary']}**")
    st.write(ticket["description"])
    st.divider()

    stored = api("GET", f"/v1/tickets/{ticket_id}/resolution")
    if stored.status_code == 200:
        render_resolution(stored.json())
    else:
        st.info("No resolution yet.")
        if st.button("🤖 Resolve with Copilot", type="primary"):
            with st.spinner("Agents working — triage → retrieval → synthesis → guardrails…"):
                resp = api("POST", f"/v1/tickets/{ticket_id}/resolve-now")
            if resp.status_code == 200:
                render_resolution(resp.json())
            else:
                st.error(resp.text)
