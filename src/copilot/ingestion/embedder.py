# converts text to embeddings
# logs model loading and failures

from sentence_transformers import SentenceTransformer
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

class Embedder:
    def __init__(self):
        try:
            logger.info("loading embedding model\n")
            self.model = SentenceTransformer(
                "all-MiniLM-L6-v2"
            )
            logger.info("embedding model loaded\n")

        except Exception:
            logger.error("failed to load embedding model\n", exc_info=True)
            raise

    def embed(self, texts):
        try:
            logger.info(f"creating embeddings for {len(texts)} chunks\n")
            return self.model.encode(texts)

        except Exception:
            logger.error("embedding creation failed\n", exc_info=True)
            raise