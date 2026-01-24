# stores embeddings and chunk metadata

import faiss
import pickle
from pathlib import Path
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

class FAISSStore:
    def __init__(self, dimension: int):
        try:
            logger.info("initializing faiss index\n")
            self.index = faiss.IndexFlatL2(dimension)
            self.metadata = []  # stores chunk dicts
            logger.info("faiss index initialized\n")

        except Exception:
            logger.error("faiss init failed\n", exc_info=True)
            raise

    def add(self, embeddings, chunks):
        try:
            logger.info(f"adding {len(chunks)} embeddings\n")

            self.index.add(embeddings)
            self.metadata.extend(chunks)

            logger.info("embeddings added\n")

        except Exception:
            logger.error("adding embeddings failed\n", exc_info=True)
            raise

    def save(self, path: Path):
        try:
            path.mkdir(parents=True, exist_ok=True)

            faiss.write_index(self.index, str(path / "index.faiss"))

            with open(path / "metadata.pkl", "wb") as f:
                pickle.dump(self.metadata, f)

            logger.info("faiss store saved\n")

        except Exception:
            logger.error("faiss save failed\n", exc_info=True)
            raise

    def load(self, path: Path):
        try:
            self.index = faiss.read_index(str(path / "index.faiss"))

            with open(path / "metadata.pkl", "rb") as f:
                self.metadata = pickle.load(f)

            logger.info("faiss store loaded\n")

        except Exception:
            logger.error("faiss load failed\n", exc_info=True)
            raise