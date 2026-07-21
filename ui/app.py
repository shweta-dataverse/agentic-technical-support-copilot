"""Internal support-engineer console.

Thin client over the FastAPI service — zero business logic here. Everything
it shows comes from the versioned HTTP API, which is the point: any frontend
team could build this same console from /openapi.json.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
import streamlit as st

API_URL = os.environ.get("COPILOT_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("COPILOT_API_KEY", "dev-key-change-me")

st.set_page_config(page_title="Support Copilot Console", page_icon="🛠", layout="wide")
st.title("🛠 Support Copilot — internal console")


def api(method: str, path: str, **kwargs: Any) -> httpx.Response:
    return httpx.request(
        method,
        f"{API_URL}{path}",
        headers={"X-API-Key": API_KEY},
        timeout=120.0,
        **kwargs,
    )


def render_resolution(result: dict[str, Any]) -> None:
    confidence = float(result.get("confidence", 0.0))
    escalate = bool(result.get("escalate", False))

    if escalate:
        st.error(
            "⚠️ **Needs human review** — the copilot escalated this ticket "
            f"(confidence {confidence:.2f})."
        )
    else:
        st.success(f"✅ Grounded resolution (confidence {confidence:.2f})")
    st.progress(confidence, text=f"confidence {confidence:.2f}")

    st.subheader("Resolution steps")
    for i, step in enumerate(result.get("resolution_steps", []), 1):
        st.markdown(f"**{i}.** {step}")

    citations = result.get("citations", [])
    if citations:
        st.subheader("Citations")
        for c in citations:
            with st.expander(f"📄 {c['doc']} — page {c['page']}"):
                st.markdown(f"> {c.get('quote_span', '')}")

    if result.get("reasoning_summary"):
        st.caption(f"Reasoning: {result['reasoning_summary']}")
    if result.get("cost_eur") is not None:
        st.caption(f"Cost: €{result['cost_eur']:.4f}")


tab_submit, tab_ticket = st.tabs(["Submit new ticket", "Existing ticket"])

with tab_submit:
    st.markdown("Runs the agent pipeline synchronously and stores the result.")
    with st.form("submit"):
        title = st.text_input("Title", placeholder="CPU goes to STOP after firmware update")
        description = st.text_area(
            "Description", placeholder="After updating to V2.9 the CPU enters STOP with SF LED on."
        )
        submitted = st.form_submit_button("Resolve ticket")
    if submitted and title and description:
        with st.spinner("Agents working — triage → retrieval → synthesis → guardrails…"):
            resp = api("POST", "/v1/resolve", json={"title": title, "description": description})
        if resp.status_code == 200:
            body = resp.json()
            st.info(f"Stored as ticket `{body['ticket_id']}`")
            render_resolution(body)
        else:
            st.error(f"{resp.status_code}: {resp.json().get('detail', resp.text)}")

with tab_ticket:
    ticket_id = st.text_input("Ticket ID", placeholder="SUP-200")
    if ticket_id:
        resp = api("GET", f"/v1/tickets/{ticket_id}")
        if resp.status_code != 200:
            st.warning(f"{resp.status_code}: {resp.json().get('detail', 'not found')}")
        else:
            ticket = resp.json()
            st.markdown(
                f"**{ticket['summary']}**  \n{ticket['description']}  \n"
                f"category: `{ticket['category']}` · severity: `{ticket['severity']}` · "
                f"source: `{ticket['source']}`"
            )
            col_run, col_view = st.columns(2)

            if col_run.button("Resolve async (queue → worker)"):
                job_resp = api("POST", f"/v1/tickets/{ticket_id}/resolve")
                if job_resp.status_code != 202:
                    st.error(job_resp.text)
                else:
                    job_id = job_resp.json()["job_id"]
                    placeholder = st.empty()
                    for _ in range(60):
                        job = api("GET", f"/v1/jobs/{job_id}").json()
                        placeholder.info(f"job `{job_id}` — **{job['status']}**")
                        if job["status"] in ("done", "failed"):
                            break
                        time.sleep(2)
                    if job["status"] == "done" and job.get("result"):
                        render_resolution(job["result"])
                    elif job["status"] == "failed":
                        st.error(f"job failed: {job.get('error_class')}")

            if col_view.button("Show stored resolution"):
                res = api("GET", f"/v1/tickets/{ticket_id}/resolution")
                if res.status_code == 200:
                    render_resolution(res.json())
                else:
                    st.warning("no resolution stored yet")
