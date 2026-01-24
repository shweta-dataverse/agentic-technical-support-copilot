# loads text from pdf
# logs progress and errors

import pdfplumber
from pathlib import Path
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

def load_pdf(pdf_path: Path):
    try:
        logger.info("starting pdf load\n")

        pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()

                if text:
                    pages.append(
                        f"page {i + 1}\n{text}"
                    )

        logger.info(f"pdf loaded, pages extracted: {len(pages)}\n")
        return pages

    except Exception as e:
        logger.error("error while loading pdf\n", exc_info=True)
        raise