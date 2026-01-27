# copilot/streamlit_app.py
import streamlit as st
import logging
from copilot.workflows.jira_workflow import build_jira_graph

# ----------------------------
# setup logger
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# initialize jira copilot workflow
# ----------------------------
jira_graph = build_jira_graph()

# ----------------------------
# call llm / agent workflow
# ----------------------------
def generate_ticket_resolution(ticket_id: str, title: str, description: str) -> str:
    # prepare ticket payload for langgraph
    ticket = {
        "ticket_id": ticket_id,
        "title": title,
        "description": description,
    }

    logger.info(f"\n\ngenerating resolution for ticket: {ticket_id}\n")
    print(f"\n\ndebug ticket payload -> {ticket}\n")

    result = jira_graph.invoke({"ticket": ticket})
    resolution = result.get("resolution", "no resolution returned by llm")

    logger.info(f"\n\ngenerated resolution for {ticket_id}\n")
    print(f"\n\ndebug resolution -> {resolution}\n")

    return resolution

# ----------------------------
# streamlit page config
# ----------------------------
st.set_page_config(
    page_title="agentic ai ticket assistant",
    page_icon="🛠️",
    layout="wide",
)

# ----------------------------
# compact purple header
# ----------------------------
st.markdown(
    """
    <div style='background: linear-gradient(to right, #6a0dad, #8e2de2);
                padding: 8px; border-radius: 8px; color: white;'>
        <h3 style='margin:0'>agentic ai ticket assistant</h3>
        <p style='margin:0; font-size:12px'>siemens simatic s7-1500 / et 200mp</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")

# ----------------------------
# predefined tickets
# ----------------------------
tickets = [
    {
        "ticket_id": "S7-1200-001",
        "title": "Hardware Configuration Inconsistent: Startup Inhibit 0x2521",
        "description": "After a hardware replacement in Cabinet 3, the CPU refuses to enter RUN mode. Diagnostic buffer reports 'Pending startup inhibit: HW configuration inconsistent (TIA portal activity).' The physical unit is marked V4.4, but the offline project is configured for V4.2. Per manual section 6.5, the device type must be changed in the device configuration to match the physical MLFB 6ES7 214-1AG40-0XB0.[3]",
    },
    {
        "ticket_id": "S7-1200-002",
        "title": "Modbus TCP Timeout: MB_CLIENT Status 80C8",
        "description": "The communication with the remote power meter (IP: 192.168.0.50) has failed. The MB_CLIENT instruction returns error code 80C8. Network ping is successful from the engineering laptop.",
    },
]

# ----------------------------
# layout: wider left column
# ----------------------------
left_col, right_col = st.columns([2, 3])

# ----------------------------
# left column: ticket selector
# ----------------------------
with left_col:
    st.subheader("open tickets")

    selected_index = st.selectbox(
        "select ticket",
        options=range(len(tickets)),
        format_func=lambda i: f"{tickets[i]['ticket_id']} | {tickets[i]['title']}",
    )

    selected_ticket = tickets[selected_index]

    st.markdown(
        f"""
        <div style='background:#f3e5ff; padding:12px; border-radius:10px;'>
            <b>ticket id:</b> {selected_ticket['ticket_id']}<br>
            <b>title:</b> {selected_ticket['title']}<br><br>
            <b>description:</b><br>
            {selected_ticket['description']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    if st.button("resolve ticket", use_container_width=True):
        resolution = generate_ticket_resolution(
            selected_ticket["ticket_id"],
            selected_ticket["title"],
            selected_ticket["description"],
        )
        st.session_state["active_ticket_id"] = selected_ticket["ticket_id"]
        st.session_state["draft_resolution"] = resolution

# ----------------------------
# right column: resolution editor
# ----------------------------
with right_col:
    st.subheader("drafted resolution")

    if "draft_resolution" in st.session_state:
        edited_resolution = st.text_area(
            "edit resolution before confirming",
            value=st.session_state["draft_resolution"],
            height=260,
        )

        col_ok, col_reject = st.columns(2)

        with col_ok:
            if st.button("confirm resolution", use_container_width=True):
                logger.info(
                    f"\n\nresolution confirmed for ticket {st.session_state['active_ticket_id']}\n"
                )
                st.success("resolution added to ticket successfully ✅")
                del st.session_state["draft_resolution"]
                del st.session_state["active_ticket_id"]

        with col_reject:
            if st.button("reject resolution", use_container_width=True):
                logger.info("\n\nresolution rejected by user\n")
                st.warning("resolution discarded ❌")
                del st.session_state["draft_resolution"]
                del st.session_state["active_ticket_id"]

    else:
        st.info("select a ticket and click 'resolve ticket' to generate a resolution")