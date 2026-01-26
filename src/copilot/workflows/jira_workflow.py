from typing import TypedDict
from langgraph.graph import StateGraph, END
from copilot.agents.jira_agent import JiraAgent

# ------------------
# State definition
# ------------------
class JiraState(TypedDict):
    ticket: dict
    resolution: str


# ------------------
# Node functions
# ------------------
jira_agent = JiraAgent()

def process_ticket(state: JiraState) -> JiraState:
    ticket = state["ticket"]
    resolution = jira_agent.handle_ticket(ticket)
    return {
        "ticket": ticket,
        "resolution": resolution
    }


# ------------------
# Build graph
# ------------------
def build_jira_graph():
    graph = StateGraph(JiraState)

    graph.add_node("process_ticket", process_ticket)
    graph.set_entry_point("process_ticket")
    graph.add_edge("process_ticket", END)

    return graph.compile()