# Evaluation results

Snapshots and comparisons produced by the evaluation plane. Live per-run
reports (`latest_report.json`) are gitignored; curated snapshots are kept.

## Golden-dataset baseline (synthesis v1.1, 11 cases)

| Metric | Value | Floor |
|---|---|---|
| retrieval recall@k | 0.938 | 0.60 |
| retrieval precision@k | 0.547 | 0.30 |
| fabricated-citation rate | 0.000 | 0.0 (max) |
| escalation accuracy | 0.909 | 0.80 |
| mean confidence (covered) | 0.894 | 0.60 |
| faithfulness (LLM judge) | 0.948 | 0.70 |
| answer relevancy (LLM judge) | 0.945 | 0.70 |

Gate: **PASSED**. Full run at `baseline_eval.txt`.

## Eval-driven improvement (the story this plane exists to tell)

1. A suspected confidence-calibration flaw was **disproven** by measurement:
   mean confidence on well-scoped cases is 0.89, not the ~0.35 seen on vague
   demo tickets.
2. The gate **found a real defect**: the synthesis model occasionally cited
   page numbers written inside chunk text (manual cross-references) rather
   than the chunk's own page — fabricated-citation rate 0.028, which failed
   the gate and caused false escalations.
3. Fixed in two layers: synthesis prompt v1.1 (cite only the block's page
   label) reduced it; the guardrail **sanitization** (drop any ungrounded
   citation) drove it to 0 by construction and lifted escalation accuracy
   from 0.82 to 0.91.

See `retrieval_comparison.md` for the FAISS+BM25 vs AI Search migration note.
