# src/copilot/agents/knowledge_agent.py
from pathlib import Path
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.vectorstore.bm25_store import BM25Store
from copilot.vectorstore.hybrid_retriever import HybridRetriever
from copilot.agents.prompts import KNOWLEDGE_AGENT_INSTRUCTION
from copilot.ingestion.embedder import Embedder
from copilot.llm.model import OllamaLLM
from copilot.llm.chains import rag_chain
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

FAISS_PATH = Path("data/processed/faiss")  # your manual/faiss store path

class KnowledgeAgent:
    def __init__(self):
        # load FAISS store
        self.faiss_store = FAISSStore(dimension=384)
        self.faiss_store.load(FAISS_PATH)

        # load BM25 store
        self.bm25_store = BM25Store.load_from_metadata(FAISS_PATH / "metadata.pkl")

        # embedder for queries
        self.embedder = Embedder()

        # hybrid retriever
        self.hybrid_retriever = HybridRetriever(
            self.faiss_store,
            self.bm25_store,
            self.embedder
        )

        # llm
        self.llm = OllamaLLM(model_name="llama3.1")

        logger.info("knowledge agent initialized\n")

    def retrieve(self, query, k=3, alpha=0.5):
        # retrieve relevant knowledge and generate answer
        logger.info(f"retrieving knowledge for query: {query}\n")

        # build agent-aware query
        enriched_query = f"""
            {KNOWLEDGE_AGENT_INSTRUCTION}
            user issue: {query} """

        answer = rag_chain(
            question=enriched_query,
            hybrid_retriever=self.hybrid_retriever,
            llm=self.llm,
            k=k,
            alpha=alpha
        )
        return answer