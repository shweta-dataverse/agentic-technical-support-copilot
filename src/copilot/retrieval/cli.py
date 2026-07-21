"""
Query the live indexes from the terminal.

Usage: python -m copilot.retrieval.cli "startup inhibit 0x2521" [--index tickets] [-k 5]
"""

from __future__ import annotations

import argparse
import sys

from copilot.retrieval.client import HybridRetriever


def main() -> int:
    parser = argparse.ArgumentParser(description="Hybrid search against AI Search")
    parser.add_argument("query")
    parser.add_argument("--index", choices=["manuals", "tickets"], default="manuals")
    parser.add_argument("-k", type=int, default=None)
    args = parser.parse_args()

    retriever = HybridRetriever.from_settings()
    if args.index == "manuals":
        for hit in retriever.search_manuals(args.query, k=args.k):
            preview = " ".join(hit.content.split())[:120]
            print(f"[{hit.score:6.3f}] p.{hit.page:<4} {preview}")
    else:
        for ticket_hit in retriever.search_tickets(args.query, k=args.k):
            preview = " ".join(ticket_hit.description.split())[:100]
            print(
                f"[{ticket_hit.score:6.3f}] {ticket_hit.ticket_id:<12} "
                f"{ticket_hit.summary[:60]} | {preview}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
