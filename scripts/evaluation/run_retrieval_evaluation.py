from pathlib import Path
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.vectorstore.bm25_store import BM25Store
from copilot.ingestion.embedder import Embedder
from copilot.vectorstore.hybrid_retriever import HybridRetriever
from copilot.evaluation.retrieval_metrics import evaluate_retrieval

# run retrieval evaluation using hybrid retriever

# load faiss store
faiss_store = FAISSStore(dimension=384)
faiss_store.load(Path("data/processed/faiss"))

# load bm25 store
bm25_store = BM25Store.load_from_metadata(Path("data/processed/faiss/metadata.pkl"))

# load embedder
embedder = Embedder()

# create hybrid retriever
hybrid_retriever = HybridRetriever(faiss_store, bm25_store, embedder)

# manual queries + expected chunk ids
queries = [
    {
        "question": "installation of s7-1500 automation system and its rules",
        "relevant_chunk_ids": [500, 990, 101, 1040, 1045]
    },
    {
        "question": "asynchronous instructions in program execution",
        "relevant_chunk_ids": [1362, 1368, 1363, 1364, 1376]
    },
    {
        "question": "basic information on cyber security",
        "relevant_chunk_ids": [273, 274, 263, 275, 283]
    },
    {
        "question": "hardware configuration of the s7-1500 automation system",
        "relevant_chunk_ids": [500, 53, 2040, 1736, 101]
    },
    {
        "question": "extended temperature range and installation altitude",
        "relevant_chunk_ids": [2162, 217, 2194, 2202, 2190]
    },
    {
        "question": "shipping and storage conditions for system modules",
        "relevant_chunk_ids": [2108, 2109, 174, 93, 960]
    }
]

# run evaluation
metrics = evaluate_retrieval(queries, hybrid_retriever, k=5, alpha=0.5)

# print results
print("average recall:", metrics["avg_recall"])
print("average precision:", metrics["avg_precision"])
print("\nper query results:")
for pq in metrics["per_query"]:
    print(f'question: {pq["question"]}')
    print(f'recall@5: {pq["recall"]} | precision@5: {pq["precision"]}')
    print(f'retrieved chunk ids: {pq["retrieved_ids"]}')
    print(f'relevant chunk ids: {pq["relevant_ids"]}\n')