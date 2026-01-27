# generate_golden_dataset.py
# creates high-quality queries + expected chunk IDs and pages
import json
import pickle
import numpy as np
from pathlib import Path
from copilot.llm.model import OllamaLLM
from copilot.vectorstore.faiss_store import FAISSStore
from copilot.ingestion.embedder import Embedder

def generate_golden_dataset(count=25, top_k=5):
    """
    generates golden dataset for retrieval evaluation
    - count: number of queries to generate
    - top_k: number of chunks to retrieve as expected
    """

    # initialize embedder, faiss, and LLM
    embedder = Embedder()
    store = FAISSStore(dimension=384)
    store.load(Path("data/processed/faiss"))
    llm = OllamaLLM(model_name="llama3.1")

    # load metadata for manual chunk inspection
    with open("data/processed/faiss/metadata.pkl", "rb") as f:
        metadata = pickle.load(f)

    golden_dataset = []

    # pick random seed chunks for generating queries
    seed_indices = np.random.choice(len(metadata), count, replace=False)
    print(f"\n[debug] generating {count} golden queries...\n")

    for idx in seed_indices:
        seed_chunk = metadata[idx]
        chunk_text = seed_chunk.get("text", {}).get("text", "")[:1200]  # limit text length

        # generate high-quality search query via LLM
        prompt = f"""
act as a technical user. write a 3-8 word search query for the text below.
return ONLY the query, no extra words, no quotes.
text: {chunk_text}
"""
        query = llm.generate(prompt).strip().split("\n")[-1]  # take last line if LLM is talkative

        # discard too short queries (<3 words)
        if len(query.split()) < 3:
            continue

        # embed query and retrieve top_k chunks
        query_vec = embedder.embed([query])[0]
        _, indices = store.index.search(np.array([query_vec]), top_k)

        expected_ids = []
        pages = []

        for i in indices[0]:
            if i != -1:
                chunk = metadata[i]
                expected_ids.append(int(chunk.get("chunk_id")))
                pages.append(int(chunk.get("page", 0)))  # page numbers start at 1

        # append to golden dataset
        golden_dataset.append({
            "query": query,
            "seed_chunk_id": int(seed_chunk.get("chunk_id")),
            "expected_ids": list(set(expected_ids)),
            "pages": list(set(pages))
        })

    # save to JSON
    output_path = Path("data/evaluation/golden_dataset.json")
    with open(output_path, "w") as f:
        json.dump(golden_dataset, f, indent=4)

    print(f"[debug] golden dataset saved to {output_path}\n")
    print(f"[debug] total queries generated: {len(golden_dataset)}")

if __name__ == "__main__":
    generate_golden_dataset(count=5, top_k=5)