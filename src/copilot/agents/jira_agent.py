# src/copilot/agents/jira_agent.py
from pathlib import Path
from copilot.agents.knowledge_agent import KnowledgeAgent
from copilot.agents.synthesis_agent import SynthesisAgent
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.vectorstore.bm25_store import BM25Store
from copilot.vectorstore.hybrid_retriever import HybridRetriever
from copilot.ingestion.embedder import Embedder
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

FAISS_JIRA_PATH = Path("data/processed/faiss/jira_jtickets")
FAISS_PATH = Path("data/processed/faiss")

class JiraAgent:
    def __init__(self):
        # load jira tickets faiss
        self.faiss_store = FAISSStore(dimension=384)
        self.faiss_store.load(FAISS_JIRA_PATH)

        # bm25 for jira tickets
        self.bm25_store = BM25Store.load_from_metadata(FAISS_PATH / "metadata.json")

        # embedder for queries
        self.embedder = Embedder()

        # hybrid retriever for jira tickets
        self.hybrid_retriever = HybridRetriever(self.faiss_store, self.bm25_store, self.embedder)

        # knowledge agent
        self.knowledge_agent = KnowledgeAgent()

        # synthesizer agent
        self.synthesizer = SynthesisAgent()

        logger.info("jira agent initialized\n")

    def handle_ticket(self, ticket):


        # check if resolution exists
        if ticket.get("resolution_summary"):
            logger.info("=====\n\nticket already resolved, no prediction generated=====\n\n")
            return ""

        query = f"{ticket['title']} \n {ticket['description']}"

        print("\nProcessing Jira Ticket:\n", query, "\n")

        # retrieve similar tickets
        logger.info("retrieving similar jira tickets\n")
        similar_tickets = self.hybrid_retriever.retrieve(query, k=3, alpha=0.5)

        if not similar_tickets:
            logger.info("no similar jira tickets found")
        else:
            logger.info(f"found {len(similar_tickets)} similar jira ticket(s)")

        for idx, ticket in enumerate(similar_tickets, start=1):
            ticket_id = ticket.get("ticket_id", "UNKNOWN")
            ticket_title = ticket.get("title", "").strip()

            
            logger.info(
                f"\n--- Similar Ticket {idx} ---\n"
                f"Ticket ID: {ticket_id}\n"
                f"Title:\n{ticket_title}\n"
            )

        # retrieve knowledge from manuals if needed
        logger.info("retrieving knowledge from knowledge agent\n")
        knowledge_context = self.knowledge_agent.retrieve(query)

        # generate final draft
        logger.info("generating final resolution using synthesizer\n")
        final_resolution = self.synthesizer.generate(ticket, similar_tickets, knowledge_context)
        return final_resolution