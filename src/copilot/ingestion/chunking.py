"""
Splits pages into chunks with stable SHA256 ids, so re-ingesting overwrites instead of
duplicating.
"""

from __future__ import annotations

import hashlib

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from copilot.config import get_settings


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    page: int
    position: int  # 0-based order of the chunk within its page
    content: str


def make_chunk_id(doc_id: str, page: int, position: int) -> str:
    return hashlib.sha256(f"{doc_id}:{page}:{position}".encode()).hexdigest()


def chunk_pages(doc_id: str, doc_title: str, pages: list[str]) -> list[Chunk]:
    """Split page texts into overlapping chunks, preserving page provenance.

    Splitting happens per page (never across pages) so every chunk carries an
    exact page number for citations.
    """
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Chunk] = []
    for page_number, page_text in enumerate(pages, start=1):
        for position, piece in enumerate(splitter.split_text(page_text)):
            chunks.append(
                Chunk(
                    chunk_id=make_chunk_id(doc_id, page_number, position),
                    doc_id=doc_id,
                    doc_title=doc_title,
                    page=page_number,
                    position=position,
                    content=piece,
                )
            )
    return chunks
