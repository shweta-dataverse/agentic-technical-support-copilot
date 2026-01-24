# retrieves relevant chunks with metadata

import numpy as np
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def retrieve(query_embedding, store, k=5):
    try:
        logger.info(f"retrieving top {k} chunks\n")

        distances, indices = store.index.search(
            np.array([query_embedding]),
            k
        )

        results = []

        for idx in indices[0]:
            chunk = store.metadata[idx]
            results.append(chunk)

        logger.info("retrieval done\n")
        return results

    except Exception:
        logger.error("retrieval failed\n", exc_info=True)
        raise