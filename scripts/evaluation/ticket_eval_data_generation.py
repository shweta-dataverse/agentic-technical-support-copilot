# copilot/evaluation/ticket_data_generation.py
import json
import pandas as pd
from copilot.workflows.jira_workflow import build_jira_graph
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

TICKETS_JSON_PATH = "data/evaluation/ticket_ground_truth.json"
TICKET_EVAL_CSV = "data/evaluation/ticket_evaluation_data.csv"

def generate_ticket_eval_data():
    # load ticket JSON
    with open(TICKETS_JSON_PATH, "r") as f:
        tickets = json.load(f)

    # build agent
    jira_graph = build_jira_graph()

    rows = []
    for ticket in tickets:
        ticket_id = ticket.get("ticket_id")
        title = ticket.get("title")
        description = ticket.get("description")
        status = ticket.get("status")
        component = ticket.get("component")
        tags = ticket.get("tags")
        actual_resolution = ticket.get("resolution_summary") or ""

        logger.info(f"\n=== processing ticket {ticket_id} ===")

        # run agent to get predicted resolution
        predicted_response = jira_graph.invoke({"ticket": ticket})

        logger.info(f"\n\n===predicted_response:  {predicted_response} ===")
        predicted_resolution = predicted_response.get("resolution", "")

        logger.info(f"\n\npredicted resolution: {predicted_resolution}")

        # prepare row for CSV
        row = {
            "ticket_id": ticket_id,
            "title": title,
            "description": description,
            "status": status,
            "component": component,
            "tags": tags,
            "predicted_resolution": predicted_resolution,
            "actual_resolution": actual_resolution
        }
        rows.append(row)

    # save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(TICKET_EVAL_CSV, index=False)
    logger.info(f"\n=== ticket evaluation CSV saved at {TICKET_EVAL_CSV} ===")

if __name__ == "__main__":
    generate_ticket_eval_data()