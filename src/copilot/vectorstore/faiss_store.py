# stores embeddings for fast similarity search only

import faiss
from pathlib import Path
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

class FAISSStore:
    def __init__(self, dimension: int):
        try:
            logger.info("initializing faiss index\n")
            self.index = faiss.IndexFlatL2(dimension)
            logger.info("faiss index initialized\n")

        except Exception:
            logger.error("failed to initialize faiss index\n", exc_info=True)
            raise

    def add(self, embeddings):
        try:
            logger.info(f"adding {len(embeddings)} embeddings to faiss\n")
            self.index.add(embeddings)
            logger.info("embeddings added successfully\n")

        except Exception:
            logger.error("failed to add embeddings to faiss\n", exc_info=True)
            raise

    def save(self, path: Path):
        try:
            logger.info("saving faiss index to disk\n")
            faiss.write_index(self.index, str(path / "index.faiss"))
            logger.info("faiss index saved\n")

        except Exception:
            logger.error("failed to save faiss index\n", exc_info=True)
            raise

    def load(self, path: Path):
        try:
            logger.info("loading faiss index from disk\n")
            self.index = faiss.read_index(str(path / "index.faiss"))
            logger.info("faiss index loaded\n")

        except Exception:
            logger.error("failed to load faiss index\n", exc_info=True)
            raise