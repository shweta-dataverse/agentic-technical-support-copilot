# splits text into chunks with metadata

from langchain_text_splitters import RecursiveCharacterTextSplitter
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def split_text(pages, source_name="s7-1500-manual"):
    try:
        logger.info("splitting text into chunks\n")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )

        chunks = []
        chunk_id = 0

        for page in pages:
            splits = splitter.split_text(page["text"])

            for split in splits:
                chunks.append({
                    "text": split,
                    "page": page["page"],
                    "source": source_name,
                    "chunk_id": chunk_id
                })
                chunk_id += 1

        logger.info(f"text split into {len(chunks)} chunks\n")
        return chunks

    except Exception:
        logger.error("text splitting failed\n", exc_info=True)
        raise