from pathlib import Path
import numpy as np
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.ingestion.embedder import Embedder
from copilot.vectorstore.retriever import retrieve

# paths
FAISS_PATH = Path("data/processed/faiss")
CHUNKS_PATH = Path("data/processed/chunks")

# load FAISS index
# dynamically detect embedding dimension
embedder = Embedder()
dummy_embedding = embedder.embed(["on "])
embedding_dim = dummy_embedding.shape[1]
print(f"detected embedding dimension: {embedding_dim}\n")

store = FAISSStore(dimension=embedding_dim)
store.load(FAISS_PATH)

# user query
query = "what are safety protocols in dangers and emergency?"
query_embedding = embedder.embed([query])[0]

# retrieve top 5 chunks
results = retrieve(query_embedding, store, k=5)

for c in results:
    print(
        f"page {c['page']} | chunk {c['chunk_id']}\n"
        f"{c['text']}\n---\n"
    )

print("\nretrieved chunks:\n")
for r in results:
    print(r, "\n---\n")