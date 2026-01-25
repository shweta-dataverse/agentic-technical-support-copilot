import numpy as np
from copilot.utils.logger import get_logger

logger = get_logger(__name__)

# evaluates retrieval using hybrid retriever

def recall_at_k(retrieved_chunks, relevant_chunk_ids, k):
    # fraction of relevant chunks found in top k
    retrieved_ids = [c["chunk_id"] for c in retrieved_chunks[:k]]
    hits = len(set(retrieved_ids) & set(relevant_chunk_ids))
    if not relevant_chunk_ids:
        return 0.0
    return hits / len(relevant_chunk_ids)

def precision_at_k(retrieved_chunks, relevant_chunk_ids, k):
    # fraction of retrieved chunks that are relevant
    retrieved_ids = [c["chunk_id"] for c in retrieved_chunks[:k]]
    hits = len(set(retrieved_ids) & set(relevant_chunk_ids))
    denom = min(k, len(retrieved_chunks))
    return hits / denom if denom > 0 else 0.0

def evaluate_retrieval(queries, retriever, k=5, alpha=0.5):
    # evaluate retrieval for a list of queries
    recalls = []
    precisions = []
    per_query_results = []

    for q in queries:
        question = q["question"]
        relevant_chunk_ids = q.get("relevant_chunk_ids", [])

        # get top k chunks from hybrid retriever
        retrieved_chunks = retriever.retrieve(question, k=k, alpha=alpha)

        # calculate metrics
        r = recall_at_k(retrieved_chunks, relevant_chunk_ids, k)
        p = precision_at_k(retrieved_chunks, relevant_chunk_ids, k)

        recalls.append(r)
        precisions.append(p)

        # store per-query results
        per_query_results.append({
            "question": question,
            "retrieved_ids": [c["chunk_id"] for c in retrieved_chunks],
            "relevant_ids": relevant_chunk_ids,
            "recall": round(r, 2),
            "precision": round(p, 2)
        })

        logger.info(f"query: {question}")
        logger.info(f"recall@{k}: {r:.2f} | precision@{k}: {p:.2f}")
        logger.info(f"retrieved ids: {[c['chunk_id'] for c in retrieved_chunks]}")
        logger.info(f"relevant ids: {relevant_chunk_ids}\n")

    # calculate average metrics
    avg_recall = float(np.mean(recalls))
    avg_precision = float(np.mean(precisions))

    return {
        "avg_recall": round(avg_recall, 2),
        "avg_precision": round(avg_precision, 2),
        "per_query": per_query_results
    }