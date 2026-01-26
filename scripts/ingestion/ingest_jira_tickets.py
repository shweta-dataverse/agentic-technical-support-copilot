# scripts/ingest_jira_tickets.py
import json
from pathlib import Path
import numpy as np
from datetime import datetime
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.ingestion.embedder import Embedder
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

DATA_PATH = Path("data/raw/jira_tickets.json")
FAISS_PATH = Path("data/processed/faiss/jira_jtickets")

def main():
    try:
        logger.info("loading jira tickets\n")
        with open(DATA_PATH, "r") as f:
            tickets = json.load(f)

        # convert tickets to text for embeddings
        texts = []
        metadatas = []
        for t in tickets:
            text = f"{t['title']}\n{t['description']}\nstatus: {t['status']}\npriority: {t['priority']}\ncomponent: {t['component']}"
            texts.append(text)

            metadatas.append({
                "ticket_id": t["ticket_id"],
                "title": t["title"],
                "status": t["status"],
                "priority": t["priority"],
                "component": t["component"],
                "created_at": t["created_at"],
                "updated_at": t["updated_at"]
            })

        logger.info("initializing embedder\n")
        embedder = Embedder()
        embeddings = embedder.embed(texts)

        logger.info(f"creating faiss store for {len(texts)} tickets\n")
        dim = embeddings.shape[1]
        faiss_store = FAISSStore(dimension=dim)
        faiss_store.add(embeddings, metadatas)

        logger.info("saving jira faiss store\n")
        faiss_store.save(FAISS_PATH)

        print("\nfaiss ingestion completed for jira tickets\n")

    except Exception:
        logger.error("jira ingestion failed\n", exc_info=True)
        raise

if __name__ == "__main__":
    main()