# finds most relevant chunks for a query

import numpy as np
from copilot.utils.logger import get_logger
import pickle
from pathlib import Path

logger = get_logger(__name__)

def retrieve(query_embedding, faiss_store, chunks_path: Path, k: int = 5):
    """
    retrieve top-k relevant chunks for a query embedding
    faiss_store: instance of FAISSStore
    chunks_path: path to texts.pkl
    """
    try:
        logger.info(f"starting retrieval with top k = {k}\n")

        # load chunks
        with open(chunks_path / "texts.pkl", "rb") as f:
            texts = pickle.load(f)

        # search FAISS index
        distances, indices = faiss_store.index.search(
            np.array([query_embedding]),
            k
        )

        results = []
        for i in indices[0]:
            results.append(texts[i])

        logger.info("retrieval completed\n")
        return results

    except Exception:
        logger.error("retrieval failed\n", exc_info=True)
        raise