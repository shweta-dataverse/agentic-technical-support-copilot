# src/copilot/agents/synthesis_agent.py
from copilot.llm.model import OllamaLLM
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

class SynthesisAgent:
    def __init__(self):
        # initialize ollama llama3 model
        self.llm = OllamaLLM(model_name="llama3.1")
        logger.info("synthesis agent initialized\n")

    def generate(self, ticket, similar_tickets=None, knowledge_context=None):

        title = ticket.get("title", "")
        description = ticket.get("description", "")

        # build prompt combining ticket, similar tickets, and knowledge
        prompt = f"""
        you are an expert siements s7-1500 automation system technical support assistant\n
        jira ticket title: {title}\n
        ticket description: {description}\n
        similar tickets: {similar_tickets}\n
        knowledge from manuals: {knowledge_context}\n
        draft a clear, actionable resolution\n
        """
        logger.info("generating resolution from llm\n")
        resolution = self.llm.generate(prompt)
        return resolution