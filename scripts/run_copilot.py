from copilot.workflows.jira_workflow import build_jira_graph
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    jira_graph = build_jira_graph()

    ticket = {
        "ticket_id": "S7-1200-001",
        "title": "Hardware Configuration Inconsistent: Startup Inhibit 0x2521",
        "description": "CPU refuses to enter RUN mode after hardware replacement..."
    }

    result = jira_graph.invoke({"ticket": ticket})

    logger.info("\n=== FINAL RESOLUTION ===\n")
    logger.info(result["resolution"])


if __name__ == "__main__":
    main()