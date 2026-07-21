"""Old-vs-new retrieval comparison: v1 FAISS+BM25 vs Azure AI Search hybrid.

Runs the 6-query v1 gold dataset (page-level ground truth) against both
systems and records page-recall@8 and MRR. This is the migration evidence
required before deleting the legacy stores; the full golden dataset arrives
with the evaluation plane.

Run: python scripts/evaluation/compare_retrieval.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from copilot.retrieval.client import HybridRetriever

K = 8
GOLD_PATH = Path("data/evaluation/manual_gold_dataset.json")
OLD_DIR = Path("data/processed/faiss")
OUT_DIR = Path("eval/results")


def load_old_corpus() -> tuple[list[str], list[int]]:
    """Extract clean text and page numbers from the v1 metadata format."""
    meta = json.loads((OLD_DIR / "metadata.json").read_text())
    texts: list[str] = []
    pages: list[int] = []
    for m in meta:
        raw = m.get("text", "")
        try:
            parsed = ast.literal_eval(raw)
            texts.append(parsed.get("text", "") if isinstance(parsed, dict) else str(raw))
        except (ValueError, SyntaxError):
            texts.append(str(raw))
        pages.append(int(m.get("page", 0)))
    return texts, pages


def old_retrieve(query: str, index, bm25, model, pages: list[int], k: int) -> list[int]:
    """Replicates the v1 rank-based fusion (alpha=0.5); returns page numbers."""
    q_emb = model.encode([query])
    _, vec_ids = index.search(np.asarray(q_emb, dtype="float32"), k)
    vector_ids = [int(i) for i in vec_ids[0] if i != -1]
    scores = bm25.get_scores(query.lower().split())
    bm25_ids = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

    fused: dict[int, float] = {}
    for rank, idx in enumerate(vector_ids):
        fused[idx] = fused.get(idx, 0.0) + 0.5 * (k - rank)
    for rank, idx in enumerate(bm25_ids):
        fused[idx] = fused.get(idx, 0.0) + 0.5 * (k - rank)
    ranked = sorted(fused, key=lambda i: fused[i], reverse=True)[:k]
    return [pages[i] for i in ranked]


def metrics(retrieved_pages: list[int], expected_pages: set[int]) -> tuple[float, float]:
    hits = expected_pages & set(retrieved_pages)
    recall = len(hits) / len(expected_pages)
    rr = 0.0
    for rank, page in enumerate(retrieved_pages, start=1):
        if page in expected_pages:
            rr = 1.0 / rank
            break
    return recall, rr


def main() -> None:
    gold = json.loads(GOLD_PATH.read_text())

    texts, pages = load_old_corpus()
    index = faiss.read_index(str(OLD_DIR / "index.faiss"))
    bm25 = BM25Okapi([t.lower().split() for t in texts])
    model = SentenceTransformer("all-MiniLM-L6-v2")
    new_retriever = HybridRetriever.from_settings()

    rows = []
    for item in gold:
        query, expected = item["query"], set(item["pages"])
        old_pages = old_retrieve(query, index, bm25, model, pages, K)
        new_pages = [h.page for h in new_retriever.search_manuals(query, k=K)]
        old_recall, old_rr = metrics(old_pages, expected)
        new_recall, new_rr = metrics(new_pages, expected)
        rows.append(
            {
                "query": query,
                "old": {"recall@8": old_recall, "mrr": old_rr},
                "new": {"recall@8": new_recall, "mrr": new_rr},
            }
        )

    def avg(system: str, metric: str) -> float:
        return sum(r[system][metric] for r in rows) / len(rows)

    summary = {
        "queries": len(rows),
        "old_faiss_bm25": {"recall@8": avg("old", "recall@8"), "mrr": avg("old", "mrr")},
        "new_ai_search_hybrid": {"recall@8": avg("new", "recall@8"), "mrr": avg("new", "mrr")},
        "notes": "page-level ground truth from v1 gold set; old system rebuilt from "
        "v1 artifacts (MiniLM 384d, 2309 chunks); new system text-embedding-3-small "
        "1536d, 1142 chunks, server-side RRF",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "retrieval_comparison.json").write_text(
        json.dumps({"summary": summary, "per_query": rows}, indent=2)
    )

    print(f"{'system':<24}{'recall@8':>10}{'mrr':>8}")
    print(f"{'old faiss+bm25':<24}{summary['old_faiss_bm25']['recall@8']:>10.3f}"
          f"{summary['old_faiss_bm25']['mrr']:>8.3f}")
    print(f"{'new ai-search hybrid':<24}{summary['new_ai_search_hybrid']['recall@8']:>10.3f}"
          f"{summary['new_ai_search_hybrid']['mrr']:>8.3f}")
    print(f"\nper-query detail written to {OUT_DIR / 'retrieval_comparison.json'}")


if __name__ == "__main__":
    main()
