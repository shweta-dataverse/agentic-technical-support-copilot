# scripts/ingest_docs.py
from pathlib import Path
import json
from copilot.ingestion.pdf_loader import load_pdf
from copilot.ingestion.text_splitter import split_text
from copilot.ingestion.embedder import Embedder
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

# file paths
PDF_PATH = Path("data/raw/manuals/s71500_et200mp_system_manual_en-US_en-US.pdf")
FAISS_PATH = Path("data/processed/faiss")
CHUNKS_PATH = Path("data/processed/chunks")

def main():
    try:
        logger.info("start ingestion pipeline")

        # load pdf pages
        pages = load_pdf(PDF_PATH)
        logger.info("loaded pages: " + str(len(pages)))

        # split each page into chunks and track page number
        chunks_metadata = []
        for page_num, page_text in enumerate(pages, start=1):
            page_chunks = split_text([page_text])  # split this page
            for chunk_text in page_chunks:
                chunk = {
                    "chunk_id": len(chunks_metadata),  # sequential id
                    "text": chunk_text,
                    "page": page_num  # store actual page number
                }
                chunks_metadata.append(chunk)
        logger.info("created chunks: " + str(len(chunks_metadata)))

        # create embeddings
        embedder = Embedder()
        embeddings = embedder.embed([chunk["text"] for chunk in chunks_metadata])
        logger.info("embeddings shape: " + str(embeddings.shape))

        # initialize faiss store and add embeddings
        store = FAISSStore(dimension=embeddings.shape[1])
        store.add(embeddings, chunks_metadata)

        # make directories if not exist
        FAISS_PATH.mkdir(parents=True, exist_ok=True)
        CHUNKS_PATH.mkdir(parents=True, exist_ok=True)

        # save faiss index and metadata
        store.save(FAISS_PATH)

        # save chunks text separately (optional)
        chunks_text_only = [chunk["text"] for chunk in chunks_metadata]
        with open(CHUNKS_PATH / "texts.json", "w", encoding="utf-8") as f:
            json.dump(chunks_text_only, f, ensure_ascii=False)

        logger.info("ingestion pipeline completed successfully")

    except Exception:
        logger.critical("ingestion pipeline failed", exc_info=True)
        raise

if __name__ == "__main__":
    main()