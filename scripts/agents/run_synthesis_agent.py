from copilot.agents.synthesis_agent import SynthesisAgent
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

ticket = {
    "ticket_id": "S7-1200-001",
    "title": "Hardware Configuration Inconsistent: Startup Inhibit 0x2521",
    "description": "After a hardware replacement in Cabinet 3, the CPU refuses to enter RUN mode..."
}

similar_tickets = [
    {"ticket_id": "S7-1200-002", "title": "CPU RUN mode error"},
    {"ticket_id": "S7-1200-003", "title": "Startup inhibit code mismatch"}
]

knowledge_context = "Manual section 6.5 states the device type must match the physical MLFB."

synth = SynthesisAgent()
resolution = synth.generate(ticket, similar_tickets, knowledge_context)

logger.info(f"generated resolution for ticket {ticket['ticket_id']}")
print(resolution)