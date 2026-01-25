from pathlib import Path
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.vectorstore.bm25_store import BM25Store
from copilot.ingestion.embedder import Embedder
from copilot.vectorstore.hybrid_retriever import HybridRetriever
from copilot.vectorstore.context_expander import expand_with_neighbors


if __name__ == "__main__":
    embedder = Embedder()
    faiss = FAISSStore(dimension=384)
    faiss.load(Path("data/processed/faiss"))

    bm25 = BM25Store.load_from_metadata(
        Path("data/processed/faiss/metadata.pkl")
    )

    hybrid_retriever = HybridRetriever(faiss, bm25, embedder)

    query = "tell overview of protection functions?"
    results = hybrid_retriever.retrieve(query, k=7)
 #   results = expand_with_neighbors(results, faiss.metadata, window=1)

    print("-------[demo] hybrid retrieval results:------\n",
           results, "\n")
    

    for r in results:
        print(
            f"page={r.get('page')}, "
            f"chunk={r.get('chunk_id')}"
        )
