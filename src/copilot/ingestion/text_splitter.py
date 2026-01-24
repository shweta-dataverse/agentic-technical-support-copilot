# splits text into smaller chunks
# needed because llms cannot read big text

from langchain_text_splitters import RecursiveCharacterTextSplitter
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def split_text(pages):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )

    chunks = []

    for page in pages:
        chunks.extend(splitter.split_text(page))

    logger.info("text split into chunks\n")
    return chunks