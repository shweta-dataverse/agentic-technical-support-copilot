# src/copilot/vectorstore/faiss_store.py

import faiss
import json
from pathlib import Path
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

class FAISSStore:
    def __init__(self, dimension: int):
        try:
            logger.info("initializing faiss index")
            self.index = faiss.IndexFlatL2(dimension)
            self.metadata = []  # list of dicts: page, chunk_id, text, etc.
            logger.info("faiss index initialized")
        except Exception:
            logger.error("faiss init failed", exc_info=True)
            raise

    def add(self, embeddings, chunks):
        """
        embeddings: np.array of shape (num_chunks, dim)
        chunks: list of dicts, each dict = {'page': int, 'chunk_id': int, 'text': str}
        """
        try:
            logger.info(f"adding {len(chunks)} embeddings to FAISS")
            self.index.add(embeddings)
            self.metadata.extend(chunks)
            logger.info("embeddings added successfully")
        except Exception:
            logger.error("adding embeddings failed", exc_info=True)
            raise

    def save(self, path: Path):
        try:
            path.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(path / "index.faiss"))

            with open(path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False)

            logger.info("faiss store saved")
        except Exception:
            logger.error("faiss save failed", exc_info=True)
            raise

    def load(self, path: Path):
        try:
            self.index = faiss.read_index(str(path / "index.faiss"))

            with open(path / "metadata.json", encoding="utf-8") as f:
                self.metadata = json.load(f)

            logger.info("faiss store loaded")
        except Exception:
            logger.error("faiss load failed", exc_info=True)
            raise