# Retrieval migration: FAISS+BM25 → Azure AI Search hybrid

Recorded 2026-07-21, 6-query v1 gold set, page-level ground truth, k=8.

| System | recall@8 | MRR |
|---|---|---|
| v1 FAISS + BM25 (MiniLM 384d, 2309 chunks, client-side fusion) | 0.869 | 1.000 |
| v2 AI Search hybrid (text-embedding-3-small 1536d, 1142 chunks, RRF) | 0.508 | 0.722 |

## Why these numbers must not be read at face value

The v1 gold set's `expected_ids` are v1 chunk indices — the dataset was
curated from the v1 retriever's own outputs. Two symptoms confirm the
label bias:

1. **v1 scores MRR 1.000 on every single query** — its first hit is always
   "relevant" because relevance was defined by what it retrieved.
2. Manual inspection of v2 results shows semantically correct hits scored
   as misses. Example, query "installation of s7-1500 and its rules":
   v2 returned p.201 ("Rules and regulations for operation") and p.180
   ("Installation Basics") — on-topic pages absent from the expected list
   because v1 never surfaced them.

This is a textbook circular-evaluation / label-leakage case: the benchmark
measures agreement with the old system, not retrieval quality.

## Consequence

The migration decision stands on architecture grounds (managed hybrid
fusion, semantic ranking, filters, zero self-managed state) and on
qualitative inspection. A fair comparison requires independently curated
labels — delivered by the evaluation plane (golden dataset, RAGAS,
retrieval metrics), which will re-baseline retrieval quality without
reference to either system's outputs.
