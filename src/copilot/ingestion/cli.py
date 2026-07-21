"""CLI entry: ingest one manual or every PDF in a directory.

Usage: python -m copilot.ingestion.cli data/raw/manuals
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from copilot.db.connection import get_session_factory
from copilot.ingestion.embedding import AzureEmbedder
from copilot.ingestion.indexer import ManualsIndexer
from copilot.ingestion.masking import PiiMasker
from copilot.ingestion.pdf import load_pdf_pages
from copilot.ingestion.pipeline import ManualIngestionPipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest PDF manuals")
    parser.add_argument("target", type=Path, help="PDF file or directory of PDFs")
    args = parser.parse_args()

    pdfs = (
        sorted(args.target.glob("*.pdf")) if args.target.is_dir() else [args.target]
    )
    if not pdfs:
        print(f"no PDFs found under {args.target}")
        return 1

    masker = PiiMasker()
    embedder = AzureEmbedder()
    indexer = ManualsIndexer()

    exit_code = 0
    with get_session_factory()() as session:
        pipeline = ManualIngestionPipeline(
            masker=masker, embedder=embedder, indexer=indexer, session=session
        )
        for pdf in pdfs:
            report = pipeline.ingest(pdf, load_pdf_pages(pdf))
            if report.skipped_unchanged:
                print(f"{report.doc_id}: unchanged, skipped")
                continue
            print(
                f"{report.doc_id}: {report.chunks_indexed}/{report.chunks_total} "
                f"chunks indexed from {report.pages} pages, "
                f"{len(report.rejected)} rejected ({report.reject_rate:.1%})"
            )
            for reject in report.rejected:
                print(f"  reject p{reject.page} {reject.chunk_id[:12]}: {reject.reason}")

    print(f"index document count: {indexer.count_documents()}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
