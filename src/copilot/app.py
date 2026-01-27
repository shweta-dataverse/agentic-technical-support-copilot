from copilot.workflows.jira_workflow import run_workflow

ticket = load_single_ticket_somehow()
resolution = run_workflow(ticket)
print("\nfinal draft resolution:\n")
print(resolution)