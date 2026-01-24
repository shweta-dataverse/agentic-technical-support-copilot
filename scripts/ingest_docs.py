from pathlib import Path

from copilot.ingestion.pdf_loader import load_pdf
from copilot.ingestion.text_splitter import split_text
from copilot.ingestion.embedder import Embedder
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.utils.logger import get_logger
import pickle

logger = get_logger(__name__)

PDF_PATH = Path("data/raw/manuals/s71500_et200mp_system_manual_en-US_en-US.pdf")

FAISS_PATH = Path("data/processed/faiss")
CHUNKS_PATH = Path("data/processed/chunks")

def main():
    try:
        logger.info("starting document ingestion pipeline\n")

        logger.info("loading pdf\n")
        pages = load_pdf(PDF_PATH)

        logger.info("splitting text into chunks\n")
        chunks = split_text(pages)

        logger.info("creating embeddings\n")
        embedder = Embedder()
        embeddings = embedder.embed(chunks)

        logger.info("initializing vector store\n")
        store = FAISSStore(embeddings.shape[1])
        store.add(embeddings, chunks)

        # make directories if not exist
        FAISS_PATH.mkdir(parents=True, exist_ok=True)
        CHUNKS_PATH.mkdir(parents=True, exist_ok=True)

        # save FAISS index
        store.save(FAISS_PATH)

        # save texts separately in chunks folder
        with open(CHUNKS_PATH / "texts.pkl", "wb") as f:
            pickle.dump(chunks, f)

        logger.info("ingestion pipeline completed successfully\n")

    except Exception:
        logger.critical("document ingestion pipeline failed\n", exc_info=True)
        raise

if __name__ == "__main__":
    main()