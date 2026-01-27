# src/copilot/scripts/run_copilot.py
# main entry for running jira copilot end-to-end
# this script calls the langgraph workflow, runs the agents, saves output in db

from copilot.workflows.jira_workflow import build_jira_graph
from copilot.utils.logger import get_logger
from copilot.db.connection import SessionLocal  # db session
from copilot.db import crud                        # db operations

logger = get_logger(__name__)

def main():
    # build the langgraph workflow (graph orchestrates jira agent -> knowledge agent -> synthesizer agent)
    jira_graph = build_jira_graph()

    # example ticket to test the workflow
    ticket = {
        "ticket_id": "S7-1200-001",
        "title": "hardware configuration inconsistent: startup inhibit 0x2521",
        "description": "cpu refuses to enter run mode after hardware replacement..."
    }

    # invoke the langgraph workflow
    result = jira_graph.invoke({"ticket": ticket})

    logger.info("\n=== FINAL RESOLUTION ===\n")
    logger.info(result["resolution"])

    # open db session to save ticket and resolution
    db = SessionLocal()

    # save ticket in db
    crud.save_ticket(db, ticket)  # ticket info stored for audit/history

    # save ai-generated resolution in db
    crud.save_resolution(db, ticket_id=ticket["ticket_id"], content=result["resolution"])  # allows later retrieval

    db.close()  # close session

    logger.info("\nrun_copilot finished: ticket and resolution saved in db\n")


if __name__ == "__main__":
    main()