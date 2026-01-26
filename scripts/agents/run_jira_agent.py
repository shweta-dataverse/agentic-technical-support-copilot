import json
from pathlib import Path
from copilot.agents.jira_agent import JiraAgent
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

JIRA_JSON_PATH = Path("data/raw/jira_tickets.json")

def main():
    try:
        logger.info("loading jira tickets\n")
        with open(JIRA_JSON_PATH, "r") as f:
            tickets = json.load(f)

        jira_agent = JiraAgent()

        # test only first ticket
        #ticket = tickets[1]

        #logger.info(f"testing jira ticket: {ticket['ticket_id']}\n")

        #resolution = jira_agent.handle_ticket(ticket)

        #print("\nfinal generated resolution:\n")
        #print(resolution)
        #print("\n")

        with open("data/raw/jira_tickets.json") as f:
            tickets = json.load(f)

        for ticket in tickets:
            logger.info(f"testing jira ticket: {ticket['ticket_id']}\n")
            print(f"\n--- Ticket {ticket['ticket_id']} ---")
            print("\nfinal generated resolution:\n")
            resolution = jira_agent.handle_ticket(ticket)
            print(resolution)

    except Exception:
        logger.error("jira agent test failed", exc_info=True)
        raise

if __name__ == "__main__":
    main()