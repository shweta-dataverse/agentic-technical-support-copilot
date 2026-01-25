# scripts/run_rag_chain.py
from pathlib import Path
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.vectorstore.bm25_store import BM25Store
from copilot.vectorstore.hybrid_retriever import HybridRetriever
from copilot.ingestion.embedder import Embedder
from copilot.llm.model import OllamaLLM
from copilot.llm.chains import rag_chain
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

FAISS_PATH = Path("data/processed/faiss")
CHUNKS_PATH = Path("data/processed/chunks")

def main():
    try:
        logger.info("loading FAISS store")
        faiss_store = FAISSStore(dimension=384)
        faiss_store.load(FAISS_PATH)

        logger.info("loading BM25 store")
        bm25_store = BM25Store.load_from_metadata(FAISS_PATH / "metadata.pkl")

        logger.info("initializing embedder")
        embedder = Embedder()

        logger.info("creating hybrid retriever")
        hybrid_retriever = HybridRetriever(faiss_store, bm25_store, embedder)

        logger.info("initializing LLM")
        llm = OllamaLLM(model_name="llama3.1")

        question = "tell about System and load power supply and its details"
        logger.info(f"running rag_chain for question: {question}")

        answer = rag_chain(
            question=question,
            hybrid_retriever=hybrid_retriever,
            llm=llm,
            k=5,
            alpha=0.5
        )

        print("\nfinal answer:\n")
        print(answer)
        print("\n")

    except Exception:
        logger.error("failed to run RAG chain", exc_info=True)
        raise

if __name__ == "__main__":
    main()